import abc
import asyncio
from anyio import create_task_group, TaskGroup  # type: ignore

from typing import Callable, Awaitable, Dict, Any, TypeVar, AsyncIterator

from .layout import (
    LayoutUpdate,
    LayoutEvent,
    AbstractLayout,
    AbstractLayout,
)
from .utils import HasAsyncResources, async_resource

_Self = TypeVar("_Self")
SendCoroutine = Callable[[Any], Awaitable[None]]
RecvCoroutine = Callable[[], Awaitable[LayoutEvent]]


class StopRendering(Exception):
    """Raised to gracefully stop :meth:`AbstractRenderer.run`"""


class AbstractRenderer(HasAsyncResources, abc.ABC):
    """A base class for implementing :class:`~idom.core.layout.Layout` renderers."""

    def __init__(self, layout: AbstractLayout) -> None:
        super().__init__()
        self._layout = layout

    @async_resource
    async def layout(self) -> AsyncIterator[AbstractLayout]:
        async with self._layout as layout:
            yield layout

    @async_resource
    async def task_group(self) -> AsyncIterator[TaskGroup]:
        async with create_task_group() as group:
            yield group

    async def run(self, send: SendCoroutine, recv: RecvCoroutine, context: Any) -> None:
        """Start an unending loop which will drive the layout.

        This will call :meth:`AbstractLayouTaskGroupTaskGroupt.render` and :meth:`AbstractLayout.trigger`
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
    async def _outgoing(self, layout: AbstractLayout, context: Any) -> Any:
        ...

    @abc.abstractmethod
    async def _incoming(
        self, layout: AbstractLayout, context: Any, message: Any
    ) -> None:
        ...


class SingleStateRenderer(AbstractRenderer):
    """Each client of the renderer will get its own model.

    ..note::
        The ``context`` parameter of :meth:`SingleStateRenderer.run` should just
        be ``None`` since it's not used.
    """

    async def _outgoing(self, layout: AbstractLayout, context: Any) -> Dict[str, Any]:
        src, new, old, error = await layout.render()
        return {"root": layout.root, "src": src, "new": new, "old": old}

    async def _incoming(
        self, layout: AbstractLayout, context: Any, event: LayoutEvent
    ) -> None:
        await layout.trigger(event)
        return None


class SharedStateRenderer(SingleStateRenderer):
    """Each client of the renderer shares the same model.

    The client's ID is indicated by the ``context`` argument of
    :meth:`SharedStateRenderer.run`
    """

    def __init__(self, layout: AbstractLayout) -> None:
        super().__init__(layout)
        self._models: Dict[str, Dict[str, Any]] = {}
        self._updates: Dict[str, asyncio.Queue[LayoutUpdate]] = {}

    @async_resource
    async def task_group(self) -> AsyncIterator[TaskGroup]:
        async with create_task_group() as group:
            await group.spawn(self._render_loop)
            yield group

    async def run(
        self, send: SendCoroutine, recv: RecvCoroutine, context: str, join: bool = False
    ) -> None:
        self._updates[context] = asyncio.Queue()
        await super().run(send, recv, context)
        if join:
            await self._join_event.wait()

    async def _render_loop(self) -> None:
        while True:
            src, new, old, error = await self.layout.render()
            # add new models to the overall state
            self._models.update(new)
            # remove old ones from the overall state
            for old_id in old:
                del self._models[old_id]
            # append updates to all other contexts
            for queue in self._updates.values():
                await queue.put(LayoutUpdate(src, new, old, error))

    async def _outgoing_loop(self, send: SendCoroutine, context: str) -> None:
        if self.layout.root in self._models:
            await send(
                {
                    "root": self.layout.root,
                    "src": self.layout.root,
                    "new": self._models,
                    "old": [],
                }
            )
        await super()._outgoing_loop(send, context)

    async def _outgoing(self, layout: AbstractLayout, context: str) -> Dict[str, Any]:
        src, new, old, error = await self._updates[context].get()
        return {"root": layout.root, "src": src, "new": new, "old": old}

    @async_resource
    async def _join_event(self) -> AsyncIterator[asyncio.Event]:
        event = asyncio.Event()
        try:
            yield event
        finally:
            event.set()
