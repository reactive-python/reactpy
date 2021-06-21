"""
Dispatchers
===========
"""

from __future__ import annotations

import sys
from asyncio import Future, Queue
from asyncio.tasks import FIRST_COMPLETED, ensure_future, gather, wait
from logging import getLogger
from typing import Any, AsyncIterator, Awaitable, Callable, List, Sequence, Tuple
from weakref import WeakSet

from anyio import create_task_group

from idom.utils import Ref

from .layout import Layout, LayoutEvent, LayoutUpdate


if sys.version_info >= (3, 7):  # pragma: no cover
    from contextlib import asynccontextmanager  # noqa
else:  # pragma: no cover
    from async_generator import asynccontextmanager


logger = getLogger(__name__)

SendCoroutine = Callable[[Any], Awaitable[None]]
RecvCoroutine = Callable[[], Awaitable[LayoutEvent]]


async def dispatch_single_view(
    layout: Layout,
    send: SendCoroutine,
    recv: RecvCoroutine,
) -> None:
    """Run a dispatch loop for a single view instance"""
    with layout:
        async with create_task_group() as task_group:
            task_group.start_soon(_single_outgoing_loop, layout, send)
            task_group.start_soon(_single_incoming_loop, layout, recv)


SharedViewDispatcher = Callable[[SendCoroutine, RecvCoroutine], Awaitable[None]]
_SharedViewDispatcherFuture = Callable[[SendCoroutine, RecvCoroutine], "Future[None]"]


@asynccontextmanager
async def create_shared_view_dispatcher(
    layout: Layout, run_forever: bool = False
) -> AsyncIterator[_SharedViewDispatcherFuture]:
    """Enter a dispatch context where all subsequent view instances share the same state"""
    with layout:
        (
            dispatch_shared_view,
            model_state,
            all_update_queues,
        ) = await _make_shared_view_dispatcher(layout)

        dispatch_tasks: List[Future[None]] = []

        def dispatch_shared_view_soon(
            send: SendCoroutine, recv: RecvCoroutine
        ) -> Future[None]:
            future = ensure_future(dispatch_shared_view(send, recv))
            dispatch_tasks.append(future)
            return future

        yield dispatch_shared_view_soon

        gathered_dispatch_tasks = gather(*dispatch_tasks, return_exceptions=True)

        while True:
            (
                update_future,
                dispatchers_completed_future,
            ) = await _wait_until_first_complete(
                layout.render(),
                gathered_dispatch_tasks,
            )

            if dispatchers_completed_future.done():
                update_future.cancel()
                break
            else:
                update: LayoutUpdate = update_future.result()

            model_state.current = update.apply_to(model_state.current)
            # push updates to all dispatcher callbacks
            for queue in all_update_queues:
                queue.put_nowait(update)


def ensure_shared_view_dispatcher_future(
    layout: Layout,
) -> Tuple[Future[None], SharedViewDispatcher]:
    """Ensure the future of a dispatcher created by :func:`create_shared_view_dispatcher`"""
    dispatcher_future: Future[SharedViewDispatcher] = Future()

    async def dispatch_shared_view_forever() -> None:
        with layout:
            (
                dispatch_shared_view,
                model_state,
                all_update_queues,
            ) = await _make_shared_view_dispatcher(layout)

            dispatcher_future.set_result(dispatch_shared_view)

            while True:
                update = await layout.render()
                model_state.current = update.apply_to(model_state.current)
                # push updates to all dispatcher callbacks
                for queue in all_update_queues:
                    queue.put_nowait(update)

    async def dispatch(send: SendCoroutine, recv: RecvCoroutine) -> None:
        await (await dispatcher_future)(send, recv)

    return ensure_future(dispatch_shared_view_forever()), dispatch


async def _make_shared_view_dispatcher(
    layout: Layout,
) -> Tuple[SharedViewDispatcher, Ref[Any], WeakSet[Queue[LayoutUpdate]]]:
    initial_update = await layout.render()
    model_state = Ref(initial_update.apply_to({}))

    # We push updates to queues instead of pushing directly to send() callbacks in
    # order to isolate the render loop from any errors dispatch callbacks might
    # raise.
    all_update_queues: WeakSet[Queue[LayoutUpdate]] = WeakSet()

    async def dispatch_shared_view(send: SendCoroutine, recv: RecvCoroutine) -> None:
        update_queue: Queue[LayoutUpdate] = Queue()
        async with create_task_group() as inner_task_group:
            all_update_queues.add(update_queue)
            await send(LayoutUpdate.create_from({}, model_state.current))
            inner_task_group.start_soon(_single_incoming_loop, layout, recv)
            inner_task_group.start_soon(_shared_outgoing_loop, send, update_queue)
        return None

    return dispatch_shared_view, model_state, all_update_queues


async def _single_outgoing_loop(layout: Layout, send: SendCoroutine) -> None:
    while True:
        await send(await layout.render())


async def _single_incoming_loop(layout: Layout, recv: RecvCoroutine) -> None:
    while True:
        await layout.dispatch(await recv())


async def _shared_outgoing_loop(
    send: SendCoroutine, queue: Queue[LayoutUpdate]
) -> None:
    while True:
        await send(await queue.get())


async def _wait_until_first_complete(
    *tasks: Awaitable[Any],
) -> Sequence[Future[Any]]:
    futures = [ensure_future(t) for t in tasks]
    await wait(futures, return_when=FIRST_COMPLETED)
    return futures
