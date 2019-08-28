import abc
import asyncio
from loguru import logger

from typing import Callable, Awaitable, Dict, Any

from .layout import Layout, LayoutUpdate, LayoutEvent, RenderError


SendCoroutine = Callable[[Any], Awaitable[None]]
RecvCoroutine = Callable[[], Awaitable[LayoutEvent]]


class AbstractRenderer(abc.ABC):
    """A base class for implementing :class:`~idom.core.layout.Layout` renderers."""

    def __init__(self, layout: Layout) -> None:
        self._layout = layout

    async def run(self, send: SendCoroutine, recv: RecvCoroutine, context: Any) -> None:
        """Start an unending loop which will drive the layout.

        This will call :meth:`Layout.render` and :meth:`Layout.trigger` to render
        new models and execute events respectively.
        """
        await asyncio.gather(
            self._outgoing_loop(send, context), self._incoming_loop(recv, context)
        )

    async def _outgoing_loop(self, send: SendCoroutine, context: Any) -> None:
        while True:
            await send(await self._outgoing(self._layout, context))

    async def _incoming_loop(self, recv: RecvCoroutine, context: Any) -> None:
        while True:
            await self._incoming(self._layout, context, await recv())

    @abc.abstractmethod
    def _outgoing(self, layout: Layout, context: Any) -> Any:
        ...

    @abc.abstractmethod
    def _incoming(self, layout: Layout, context: Any, message: Any) -> Awaitable[None]:
        ...


class SingleStateRenderer(AbstractRenderer):
    """Each client of the renderer will get its own model.

    ..note::
        The ``context`` parameter of :meth:`SingleStateRenderer.run` should just
        be ``None`` since it's not used.
    """

    async def _outgoing(self, layout: Layout, context: Any) -> Dict[str, Any]:
        try:
            src, new, old = await layout.render()
        except RenderError as error:
            if error.partial_render is None:
                raise
            logger.exception("Render failed")
            src, new, old = error.partial_render

        return {"root": layout.root, "src": src, "new": new, "old": old}

    async def _incoming(self, layout: Layout, context: Any, event: LayoutEvent) -> None:
        await layout.trigger(event)


class SharedStateRenderer(SingleStateRenderer):
    """Each client of the renderer shares the same model.

    The client's ID is indicated by the ``context`` argument of
    :meth:`SharedStateRenderer.run`
    """

    def __init__(self, layout: Layout) -> None:
        super().__init__(layout)
        self._models: Dict[str, Dict[str, Any]] = {}
        self._updates: Dict[str, asyncio.Queue[LayoutUpdate]] = {}
        self._render_task = asyncio.ensure_future(self._render_loop(), loop=layout.loop)

    async def run(self, send: SendCoroutine, recv: RecvCoroutine, context: str) -> None:
        self._updates[context] = asyncio.Queue()
        try:
            await asyncio.gather(super().run(send, recv, context), self._render_task)
        except Exception:
            del self._updates[context]
            raise

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

    async def _outgoing(self, layout: Layout, context: str) -> Dict[str, Any]:
        src, new, old = await self._updates[context].get()
        return {"root": layout.root, "src": src, "new": new, "old": old}

    def __del__(self) -> None:
        self._render_task.cancel()
