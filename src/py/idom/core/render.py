import abc
import asyncio

from typing import Callable, Awaitable, Dict, Any

from .layout import Layout, RenderBundle


CoroutineFunction = Callable[..., Awaitable[Any]]


class AbstractRenderer(abc.ABC):
    def __init__(self, layout: Layout) -> None:
        self._layout = layout

    async def run(
        self, send: CoroutineFunction, recv: CoroutineFunction, context: Any
    ) -> None:
        await asyncio.gather(
            self._outgoing_loop(send, context), self._incoming_loop(recv, context)
        )

    async def _outgoing_loop(self, send: CoroutineFunction, context: Any) -> None:
        while True:
            await send(await self._outgoing(self._layout, context))

    async def _incoming_loop(self, recv: CoroutineFunction, context: Any) -> None:
        while True:
            await self._incoming(self._layout, context, await recv())

    @abc.abstractmethod
    def _outgoing(self, layout: Layout, context: Any) -> Any:
        ...

    @abc.abstractmethod
    def _incoming(self, layout: Layout, context: Any, message: Any) -> Awaitable[None]:
        ...


class SingleStateRenderer(AbstractRenderer):
    async def _outgoing(self, layout: Layout, context: Any) -> Dict[str, Any]:
        src, new, old = await layout.render()
        return {"root": layout.root, "src": src, "new": new, "old": old}

    async def _incoming(self, layout: Layout, context: Any, message: Any) -> None:
        await layout.trigger(**message)


class SharedStateRenderer(SingleStateRenderer):
    def __init__(self, layout: Layout) -> None:
        super().__init__(layout)
        self._models: Dict[str, Dict[str, Any]] = {}
        self._updates: Dict[str, asyncio.Queue[RenderBundle]] = {}
        self._render_task = asyncio.ensure_future(
            self._render_loop(), loop=self._layout.loop
        )

    async def run(
        self, send: CoroutineFunction, recv: CoroutineFunction, context: str
    ) -> None:
        self._updates[context] = asyncio.Queue()
        try:
            await asyncio.gather(super().run(send, recv, context), self._render_task)
        except Exception:
            del self._updates[context]
            raise

    async def _render_loop(self) -> None:
        while True:
            src, new, old = await self._layout.render()
            # add new models to the overall state
            self._models.update(new)
            # remove old ones from the overall state
            for old_id in old:
                del self._models[old_id]
            # append updates to all other contexts
            for queue in self._updates.values():
                queue.put((src, new, old))

    async def _outgoing_loop(self, send: CoroutineFunction, context: str) -> None:
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
