import abc
import asyncio
from weakref import finalize

from typing import Callable, Awaitable, Dict, Set, Tuple, Any, List

from .layout import Layout, RenderType


CoroutineFunction = Callable[..., Awaitable[Any]]


class BaseRenderer(abc.ABC):
    def __init__(self, layout: Layout):
        self._layout = layout

    async def run(self, send: CoroutineFunction, recv: CoroutineFunction, context: Any):
        await asyncio.gather(
            self._outgoing_loop(send, context), self._incoming_loop(recv, context)
        )

    async def _outgoing_loop(self, send: CoroutineFunction, context: Any):
        while True:
            await send(await self._outgoing(self._layout, context))

    async def _incoming_loop(self, recv: CoroutineFunction, context: Any):
        while True:
            await self._incoming(self._layout, context, await recv())

    @abc.abstractmethod
    def _outgoing(self, layout: Layout, context: Any) -> Any:
        ...

    @abc.abstractmethod
    def _incoming(self, layout: Layout, context: Any, message: Any):
        ...


class SingleStateRenderer(BaseRenderer):
    async def _outgoing(self, layout, context) -> Dict:
        roots, new, old = await layout.render()
        return {"roots": roots, "new": new, "old": old}

    async def _incoming(self, layout, context, message):
        await layout.apply(**message)


class SharedStateRenderer(SingleStateRenderer):
    def __init__(self, layout):
        super().__init__(layout)
        self._models: Dict[str, Dict] = {}
        self._contexts: Dict[str, Tuple[List[RenderType], asyncio.Event]] = {}
        self._render_task = asyncio.ensure_future(
            self._render_loop(), loop=self._layout.loop
        )
        finalize(self, lambda t: t.cancel(), self._render_task)

    async def run(self, send, recv, context: str):
        self._contexts[context] = ([], asyncio.Event())
        try:
            await asyncio.gather(super().run(send, recv, context), self._render_task)
        except Exception:
            del self._contexts[context]
            raise

    async def _render_loop(self):
        while True:
            roots, new, old = await self._layout.render()
            # add new models to the overall state
            self._models.update(new)
            # remove old ones from the overall state
            for old_id in old:
                del self._models[old_id]
            # append updates to all other contexts
            for updates, event in self._contexts.values():
                updates.append((roots, new, old))
                event.set()

    async def _outgoing_loop(self, send, context: str):
        if self._layout.root in self._models:
            await send({"roots": [self._layout.root], "new": self._models, "old": []})
        await super()._outgoing_loop(send, context)

    async def _outgoing(self, layout, context: str) -> Dict:
        updates, event = self._contexts[context]
        await event.wait()
        # wait for another context to receive an update
        transient_old: Set[str] = set()
        roots = set()
        new = {}
        for r, n, o in reversed(updates):
            # add models not marked as old
            for key, model in n.items():
                if key not in o:
                    new[key] = model
            # add all old model ids
            transient_old.update(o)
            # add roots which were not marked as old
            roots.update(set(r).difference(transient_old))
        # old models from the intermediate updates were already excluded
        old = transient_old.difference(new)
        updates.clear()
        event.clear()
        return {"roots": list(roots), "new": new, "old": list(old)}
