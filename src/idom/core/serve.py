from __future__ import annotations

from asyncio import ensure_future
from asyncio.tasks import ensure_future
from logging import getLogger
from typing import Any, Awaitable, Callable, Dict, List, NamedTuple, cast

from anyio import create_task_group
from jsonpatch import apply_patch

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
    """Stop serving changes and events

    Raising this error will tell dispatchers to gracefully exit. Typically this is
    called by code running inside a layout to tell it to stop rendering.
    """


async def serve_json_patch(
    layout: LayoutType[LayoutUpdate, LayoutEvent],
    send: SendCoroutine,
    recv: RecvCoroutine,
) -> None:
    """Run a dispatch loop for a single view instance"""
    async with layout:
        try:
            async with create_task_group() as task_group:
                task_group.start_soon(_single_outgoing_loop, layout, send)
                task_group.start_soon(_single_incoming_loop, layout, recv)
        except Stop:
            logger.info("Stopped dispatch task")


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
        return cls(update.path, [{"op": "replace", "path": "", "value": update.new}])


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
