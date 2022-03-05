from __future__ import annotations

from asyncio import Future, Queue, ensure_future
from asyncio.tasks import FIRST_COMPLETED, ensure_future, gather, wait
from contextlib import asynccontextmanager
from logging import getLogger
from typing import (
    Any,
    AsyncIterator,
    Awaitable,
    Callable,
    Dict,
    List,
    NamedTuple,
    Sequence,
    Tuple,
    cast,
)
from weakref import WeakSet

from anyio import create_task_group

from idom.utils import Ref

from ._fixed_jsonpatch import apply_patch, make_patch  # type: ignore
from .layout import LayoutEvent, LayoutUpdate
from .types import LayoutType, VdomJson


logger = getLogger(__name__)


SendCoroutine = Callable[["VdomJsonPatch"], Awaitable[None]]
"""Send model patches given by a dispatcher"""

RecvCoroutine = Callable[[], Awaitable[LayoutEvent]]
"""Called by a dispatcher to return a :class:`idom.core.layout.LayoutEvent`

The event will then trigger an :class:`idom.core.proto.EventHandlerType` in a layout.
"""


class Stop(BaseException):
    """Stop dispatching changes and events

    Raising this error will tell dispatchers to gracefully exit. Typically this is
    called by code running inside a layout to tell it to stop rendering.
    """


async def dispatch_single_view(
    layout: LayoutType[LayoutUpdate, LayoutEvent],
    send: SendCoroutine,
    recv: RecvCoroutine,
) -> None:
    """Run a dispatch loop for a single view instance"""
    with layout:
        try:
            async with create_task_group() as task_group:
                task_group.start_soon(_single_outgoing_loop, layout, send)
                task_group.start_soon(_single_incoming_loop, layout, recv)
        except Stop:
            logger.info("Stopped dispatch task")


SharedViewDispatcher = Callable[[SendCoroutine, RecvCoroutine], Awaitable[None]]
_SharedViewDispatcherFuture = Callable[[SendCoroutine, RecvCoroutine], "Future[None]"]


@asynccontextmanager
async def create_shared_view_dispatcher(
    layout: LayoutType[LayoutUpdate, LayoutEvent],
) -> AsyncIterator[_SharedViewDispatcherFuture]:
    """Enter a dispatch context where all subsequent view instances share the same state"""
    with layout:
        (
            dispatch_shared_view,
            send_patch,
        ) = await _create_shared_view_dispatcher(layout)

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
                patch = VdomJsonPatch.create_from(update_future.result())

            send_patch(patch)


def ensure_shared_view_dispatcher_future(
    layout: LayoutType[LayoutUpdate, LayoutEvent],
) -> Tuple[Future[None], SharedViewDispatcher]:
    """Ensure the future of a dispatcher made by :func:`create_shared_view_dispatcher`

    This returns a future that can be awaited to block until all dispatch tasks have
    completed as well as the dispatcher coroutine itself which is used to start dispatch
    tasks.

    This is required in situations where usage of the async context manager from
    :func:`create_shared_view_dispatcher` is not possible. Typically this happens when
    integrating IDOM with other frameworks, servers, or applications.
    """
    dispatcher_future: Future[SharedViewDispatcher] = Future()

    async def dispatch_shared_view_forever() -> None:
        with layout:
            (
                dispatch_shared_view,
                send_patch,
            ) = await _create_shared_view_dispatcher(layout)

            dispatcher_future.set_result(dispatch_shared_view)

            while True:
                send_patch(await render_json_patch(layout))

    async def dispatch(send: SendCoroutine, recv: RecvCoroutine) -> None:
        await (await dispatcher_future)(send, recv)

    return ensure_future(dispatch_shared_view_forever()), dispatch


async def render_json_patch(layout: LayoutType[LayoutUpdate, Any]) -> VdomJsonPatch:
    """Render a class:`VdomJsonPatch` from a layout"""
    return VdomJsonPatch.create_from(await layout.render())


class VdomJsonPatch(NamedTuple):
    """An object describing an update to a :class:`Layout` in the form of a JSON patch"""

    path: str
    """The path where changes should be applied"""

    changes: List[Dict[str, Any]]
    """A list of JSON patches to apply at the given path"""

    def apply_to(self, model: VdomJson) -> VdomJson:
        """Return the model resulting from the changes in this update"""
        return cast(
            VdomJson,
            apply_patch(
                model, [{**c, "path": self.path + c["path"]} for c in self.changes]
            ),
        )

    @classmethod
    def create_from(cls, update: LayoutUpdate) -> VdomJsonPatch:
        """Return a patch given an layout update"""
        return cls(update.path, make_patch(update.old or {}, update.new).patch)


async def _create_shared_view_dispatcher(
    layout: LayoutType[LayoutUpdate, LayoutEvent],
) -> Tuple[SharedViewDispatcher, Callable[[VdomJsonPatch], None]]:
    update = await layout.render()
    model_state = Ref(update.new)

    # We push updates to queues instead of pushing directly to send() callbacks in
    # order to isolate send_patch() from any errors send() callbacks might raise.
    all_patch_queues: WeakSet[Queue[VdomJsonPatch]] = WeakSet()

    async def dispatch_shared_view(send: SendCoroutine, recv: RecvCoroutine) -> None:
        patch_queue: Queue[VdomJsonPatch] = Queue()
        try:
            async with create_task_group() as inner_task_group:
                all_patch_queues.add(patch_queue)
                effective_update = LayoutUpdate("", None, model_state.current)
                await send(VdomJsonPatch.create_from(effective_update))
                inner_task_group.start_soon(_single_incoming_loop, layout, recv)
                inner_task_group.start_soon(_shared_outgoing_loop, send, patch_queue)
        except Stop:
            logger.info("Stopped dispatch task")
        finally:
            all_patch_queues.remove(patch_queue)
        return None

    def send_patch(patch: VdomJsonPatch) -> None:
        model_state.current = patch.apply_to(model_state.current)
        for queue in all_patch_queues:
            queue.put_nowait(patch)

    return dispatch_shared_view, send_patch


async def _single_outgoing_loop(
    layout: LayoutType[LayoutUpdate, LayoutEvent], send: SendCoroutine
) -> None:
    while True:
        await send(await render_json_patch(layout))


async def _single_incoming_loop(
    layout: LayoutType[LayoutUpdate, LayoutEvent], recv: RecvCoroutine
) -> None:
    while True:
        # We need to fire and forget here so that we avoid waiting on the completion
        # of this event handler before receiving and running the next one.
        ensure_future(layout.deliver(await recv()))


async def _shared_outgoing_loop(
    send: SendCoroutine, queue: Queue[VdomJsonPatch]
) -> None:
    while True:
        await send(await queue.get())


async def _wait_until_first_complete(
    *tasks: Awaitable[Any],
) -> Sequence[Future[Any]]:
    futures = [ensure_future(t) for t in tasks]
    await wait(futures, return_when=FIRST_COMPLETED)
    return futures
