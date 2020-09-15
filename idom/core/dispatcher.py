import abc
import asyncio
from typing import Callable, Awaitable, Dict, Any, AsyncIterator

from anyio import create_task_group
from anyio.abc import TaskGroup

from .layout import (
    LayoutEvent,
    LayoutUpdate,
    Layout,
)
from .utils import HasAsyncResources, async_resource

SendCoroutine = Callable[[Any], Awaitable[None]]
RecvCoroutine = Callable[[], Awaitable[LayoutEvent]]


class AbstractDispatcher(HasAsyncResources, abc.ABC):
    """A base class for implementing :class:`~idom.core.layout.Layout` dispatchers."""

    __slots__ = "_layout"

    def __init__(self, layout: Layout) -> None:
        super().__init__()
        self._layout = layout

    async def start(self) -> None:
        await self.__aenter__()

    async def stop(self) -> None:
        await self.task_group.cancel_scope.cancel()
        await self.__aexit__(None, None, None)

    @async_resource
    async def layout(self) -> AsyncIterator[Layout]:
        async with self._layout as layout:
            yield layout

    @async_resource
    async def task_group(self) -> AsyncIterator[TaskGroup]:
        async with create_task_group() as group:
            yield group

    async def run(self, send: SendCoroutine, recv: RecvCoroutine, context: Any) -> None:
        """Start an unending loop which will drive the layout.

        This will call :meth:`AbstractLayouTaskGroupTaskGroupt.render` and :meth:`Layout.dispatch`
        to render new models and execute events respectively.
        """
        await self.task_group.spawn(self._outgoing_loop, send, context)
        await self.task_group.spawn(self._incoming_loop, recv, context)
        return None

    async def _outgoing_loop(self, send: SendCoroutine, context: Any) -> None:
        while True:
            await send(await self._outgoing(self.layout, context))

    async def _incoming_loop(self, recv: RecvCoroutine, context: Any) -> None:
        while True:
            await self._incoming(self.layout, context, await recv())

    @abc.abstractmethod
    async def _outgoing(self, layout: Layout, context: Any) -> Any:
        ...

    @abc.abstractmethod
    async def _incoming(self, layout: Layout, context: Any, message: Any) -> None:
        ...


class SingleViewDispatcher(AbstractDispatcher):
    """Each client of the dispatcher will get its own model.

    ..note::
        The ``context`` parameter of :meth:`SingleViewDispatcher.run` should just
        be ``None`` since it's not used.
    """

    __slots__ = "_current_model_as_json"

    def __init__(self, layout: Layout) -> None:
        super().__init__(layout)
        self._current_model_as_json = ""

    async def _outgoing(self, layout: Layout, context: Any) -> LayoutUpdate:
        return await layout.render()

    async def _incoming(self, layout: Layout, context: Any, event: LayoutEvent) -> None:
        await layout.dispatch(event)
        return None


class SharedViewDispatcher(SingleViewDispatcher):
    """Each client of the dispatcher shares the same model.

    The client's ID is indicated by the ``context`` argument of
    :meth:`SharedViewDispatcher.run`
    """

    __slots__ = "_update_queues", "_model_state"

    def __init__(self, layout: Layout) -> None:
        super().__init__(layout)
        self._model_state: Any = {}
        self._update_queues: Dict[str, asyncio.Queue[LayoutUpdate]] = {}

    @async_resource
    async def task_group(self) -> AsyncIterator[TaskGroup]:
        async with create_task_group() as group:
            await group.spawn(self._render_loop)
            yield group

    async def run(
        self, send: SendCoroutine, recv: RecvCoroutine, context: str, join: bool = False
    ) -> None:
        await super().run(send, recv, context)
        if join:
            await self._join_event.wait()

    async def _render_loop(self) -> None:
        while True:
            update = await super()._outgoing(self.layout, None)
            self._model_state = update.apply_to(self._model_state)
            # append updates to all other contexts
            for queue in self._update_queues.values():
                await queue.put(update)

    async def _outgoing_loop(self, send: SendCoroutine, context: Any) -> None:
        self._update_queues[context] = asyncio.Queue()
        await send(LayoutUpdate.create_from({}, self._model_state))
        await super()._outgoing_loop(send, context)

    async def _outgoing(self, layout: Layout, context: str) -> LayoutUpdate:
        return await self._update_queues[context].get()

    @async_resource
    async def _join_event(self) -> AsyncIterator[asyncio.Event]:
        event = asyncio.Event()
        try:
            yield event
        finally:
            event.set()
