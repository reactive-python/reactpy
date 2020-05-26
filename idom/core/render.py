import sys
import abc
import asyncio
from anyio import create_task_group

from typing import Callable, Awaitable, Dict, Any, Union, TypeVar

from .layout import (
    LayoutUpdate,
    LayoutEvent,
    AbstractLayout,
    AbstractLayout,
)
from .utils import AsyncOpenClose, must_by_open

_Self = TypeVar("_Self")
SendCoroutine = Callable[[Any], Awaitable[None]]
RecvCoroutine = Callable[[], Awaitable[LayoutEvent]]


class StopRendering(Exception):
    """Raised to gracefully stop :meth:`AbstractRenderer.run`"""


class AbstractRenderer(AsyncOpenClose, abc.ABC):
    """A base class for implementing :class:`~idom.core.layout.Layout` renderers."""

    def __init__(self, layout: AbstractLayout) -> None:
        super().__init__()
        self._layout = layout

    @property
    def layout(self) -> AbstractLayout:
        return self._layout

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        return self._layout.loop

    async def open(self) -> None:
        await super().open()
        await self.layout.open()
        return None

    async def close(self) -> None:
        await self.layout.close()
        await super().close()
        return None

    @must_by_open()
    async def run(self, send: SendCoroutine, recv: RecvCoroutine, context: Any) -> None:
        """Start an unending loop which will drive the layout.

        This will call :meth:`AbstractLayouTaskGroupTaskGroupt.render` and :meth:`AbstractLayout.trigger`
        to render new models and execute events respectively.
        """
        async with create_task_group() as group:
            await group.spawn(self._outgoing_loop, send, context)
            await group.spawn(self._incoming_loop, recv, context)
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

    _render_task: "Union[asyncio.Task[Any], asyncio.Future[Any]]"

    def __init__(self, layout: AbstractLayout) -> None:
        super().__init__(layout)
        self.task_group = create_task_group()
        self._models: Dict[str, Dict[str, Any]] = {}
        self._updates: Dict[str, asyncio.Queue[LayoutUpdate]] = {}
        self._join_event = asyncio.Event()
        self._joining = False

    async def run(
        self, send: SendCoroutine, recv: RecvCoroutine, context: str, join: bool = False
    ) -> None:
        self._updates[context] = asyncio.Queue()
        await self.task_group.spawn(super().run, send, recv, context)
        if join:
            await self._join_event.wait()

    async def open(self) -> None:
        await super().open()
        await self.task_group.__aenter__()
        self._render_task = asyncio.ensure_future(self._render_loop(), loop=self.loop)
        return None

    async def close(self) -> None:
        try:
            try:
                await self.task_group.__aexit__(*sys.exc_info())
            finally:
                self._render_task.cancel()
            await super().close()
        finally:
            self._join_event.set()
        return None

    async def _render_loop(self) -> None:
        while True:
            src, new, old, error = await self._layout.render()
            # add new models to the overall state
            self._models.update(new)
            # remove old ones from the overall state
            for old_id in old:
                del self._models[old_id]
            # append updates to all other contexts
            for queue in self._updates.values():
                await queue.put(LayoutUpdate(src, new, old, error))

    async def _outgoing_loop(self, send: SendCoroutine, context: str) -> None:
        if self._layout.root in self._models:
            await send(
                {
                    "root": self._layout.root,
                    "src": self._layout.root,
                    "new": self._models,
                    "old": [],
                }
            )
        await super()._outgoing_loop(send, context)

    async def _outgoing(self, layout: AbstractLayout, context: str) -> Dict[str, Any]:
        src, new, old, error = await self._updates[context].get()
        return {"root": layout.root, "src": src, "new": new, "old": old}
