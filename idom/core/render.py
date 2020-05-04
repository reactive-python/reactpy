import abc
import asyncio
from anyio import create_task_group
from anyio.exceptions import ExceptionGroup
from loguru import logger

from types import TracebackType
from typing import Callable, Awaitable, Dict, Any, Optional, Type

from .layout import (
    LayoutUpdate,
    LayoutEvent,
    RenderError,
    AbstractLayout,
    AbstractLayout,
)


SendCoroutine = Callable[[Any], Awaitable[None]]
RecvCoroutine = Callable[[], Awaitable[LayoutEvent]]


class StopRendering(Exception):
    """Raised to gracefully stop :meth:`AbstractRenderer.run`"""


class AbstractRenderer(abc.ABC):
    """A base class for implementing :class:`~idom.core.layout.Layout` renderers."""

    def __init__(self, layout: AbstractLayout) -> None:
        self._layout = layout

    @property
    def layout(self) -> AbstractLayout:
        return self._layout

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        return self._layout.loop

    async def run(self, send: SendCoroutine, recv: RecvCoroutine, context: Any) -> None:
        """Start an unending loop which will drive the layout.

        This will call :meth:`AbstractLayout.render` and :meth:`AbstractLayout.trigger`
        to render new models and execute events respectively.
        """
        try:
            async with create_task_group() as group:
                await group.spawn(self._outgoing_loop, send, context)
                await group.spawn(self._incoming_loop, recv, context)
        except ExceptionGroup as error:
            for exc in error.exceptions:
                if not isinstance(exc, StopRendering):
                    raise exc
        except StopRendering:
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
        try:
            src, new, old = await layout.render()
        except RenderError as error:
            if error.partial_render is None:
                raise
            logger.exception("Render failed")
            src, new, old = error.partial_render

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

    _render_task: asyncio.Task

    def __init__(self, layout: AbstractLayout) -> None:
        super().__init__(layout)
        self._models: Dict[str, Dict[str, Any]] = {}
        self._updates: Dict[str, asyncio.Queue[LayoutUpdate]] = {}
        self._task_group = create_task_group()
        self._join_event = asyncio.Event()
        self._active = False
        self._joining = False

    async def start(self):
        await self.__aenter__()

    async def join(self):
        await self.__aexit__(None, None, None)

    async def __aenter__(self):
        if self._active:
            raise RuntimeError("Renderer already active")
        self._active = True
        await self._task_group.__aenter__()
        self._render_task = asyncio.ensure_future(self._render_loop(), loop=self.loop)
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        try:
            if not self._joining:
                self._joining = True
                try:
                    await self._task_group.__aexit__(exc_type, exc_val, exc_tb)
                finally:
                    self._render_task.cancel()
                    self._join_event.set()
                    self._join_event.clear()
            else:
                await self._join_event.wait()
        finally:
            self._active = False
            self._joining = False

    async def run(
        self, send: SendCoroutine, recv: RecvCoroutine, context: str, join: bool = False
    ) -> None:
        self._updates[context] = asyncio.Queue()
        await self._task_group.spawn(super().run, send, recv, context)
        if join:
            await self.join()

    async def _render_loop(self) -> None:
        while True:
            try:
                src, new, old = await self._layout.render()
            except RenderError as error:
                if error.partial_render is None:
                    raise
                logger.exception("Render failed")
                src, new, old = error.partial_render

            # add new models to the overall state
            self._models.update(new)
            # remove old ones from the overall state
            for old_id in old:
                del self._models[old_id]
            # append updates to all other contexts
            for queue in self._updates.values():
                await queue.put(LayoutUpdate(src, new, old))

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
        src, new, old = await self._updates[context].get()
        return {"root": layout.root, "src": src, "new": new, "old": old}
