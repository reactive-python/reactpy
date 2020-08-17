import abc
import asyncio
import json
from typing import Callable, Awaitable, Dict, Any, AsyncIterator

from anyio import create_task_group, TaskGroup  # type: ignore
from diff_match_patch import diff

from .layout import (
    LayoutEvent,
    AbstractLayout,
    AbstractLayout,
)
from .utils import HasAsyncResources, async_resource

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

    def __init__(self, layout: AbstractLayout) -> None:
        super().__init__(layout)
        self._current_model_as_json = ""

    async def _outgoing(self, layout: AbstractLayout, context: Any) -> str:
        new_current_model_as_json = json.dumps(await layout.render())
        patch = diff(
            self._current_model_as_json,
            new_current_model_as_json,
            as_patch=True,
            timelimit=0,
        )
        self._current_model_as_json = new_current_model_as_json
        return patch

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
        self._update_queues: Dict[str, asyncio.Queue[str]] = {}

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
            patch = await super()._outgoing(self.layout, None)
            # append updates to all other contexts
            for queue in self._update_queues.values():
                await queue.put(patch)

    async def _outgoing_loop(self, send: SendCoroutine, context: str) -> None:
        await super()._outgoing_loop(send, context)

    async def _outgoing(self, layout: AbstractLayout, context: str) -> str:
        return await self._updates[context].get()

    @async_resource
    async def _join_event(self) -> AsyncIterator[asyncio.Event]:
        event = asyncio.Event()
        try:
            yield event
        finally:
            event.set()
