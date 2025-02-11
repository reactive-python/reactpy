from __future__ import annotations

from collections.abc import Awaitable
from logging import getLogger
from typing import Any, Callable
from warnings import warn

from anyio import create_task_group
from anyio.abc import TaskGroup

from reactpy.config import REACTPY_DEBUG
from reactpy.core._life_cycle_hook import HOOK_STACK
from reactpy.types import LayoutEventMessage, LayoutType, LayoutUpdateMessage

logger = getLogger(__name__)


SendCoroutine = Callable[[LayoutUpdateMessage | dict[str, Any]], Awaitable[None]]
"""Send model patches given by a dispatcher"""

RecvCoroutine = Callable[[], Awaitable[LayoutEventMessage | dict[str, Any]]]
"""Called by a dispatcher to return a :class:`reactpy.core.layout.LayoutEventMessage`

The event will then trigger an :class:`reactpy.core.proto.EventHandlerType` in a layout.
"""


class Stop(BaseException):
    """Deprecated

    Stop serving changes and events

    Raising this error will tell dispatchers to gracefully exit. Typically this is
    called by code running inside a layout to tell it to stop rendering.
    """


async def serve_layout(
    layout: LayoutType[
        LayoutUpdateMessage | dict[str, Any], LayoutEventMessage | dict[str, Any]
    ],
    send: SendCoroutine,
    recv: RecvCoroutine,
) -> None:
    """Run a dispatch loop for a single view instance"""
    async with layout:
        try:
            async with create_task_group() as task_group:
                task_group.start_soon(_single_outgoing_loop, layout, send)
                task_group.start_soon(_single_incoming_loop, task_group, layout, recv)
        except Stop:  # nocov
            warn(
                "The Stop exception is deprecated and will be removed in a future version",
                UserWarning,
                stacklevel=1,
            )
            logger.info(f"Stopped serving {layout}")


async def _single_outgoing_loop(
    layout: LayoutType[
        LayoutUpdateMessage | dict[str, Any], LayoutEventMessage | dict[str, Any]
    ],
    send: SendCoroutine,
) -> None:
    while True:
        token = HOOK_STACK.initialize()
        try:
            update = await layout.render()
            try:
                await send(update)
            except Exception:  # nocov
                if not REACTPY_DEBUG.current:
                    msg = (
                        "Failed to send update. More info may be available "
                        "if you enabling debug mode by setting "
                        "`reactpy.config.REACTPY_DEBUG.current = True`."
                    )
                    logger.error(msg)
                raise
        finally:
            HOOK_STACK.reset(token)


async def _single_incoming_loop(
    task_group: TaskGroup,
    layout: LayoutType[
        LayoutUpdateMessage | dict[str, Any], LayoutEventMessage | dict[str, Any]
    ],
    recv: RecvCoroutine,
) -> None:
    while True:
        # We need to fire and forget here so that we avoid waiting on the completion
        # of this event handler before receiving and running the next one.
        task_group.start_soon(layout.deliver, await recv())
