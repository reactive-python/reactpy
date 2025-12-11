from __future__ import annotations

from collections.abc import Awaitable, Callable
from logging import getLogger
from typing import Any

from anyio import create_task_group
from anyio.abc import TaskGroup

from reactpy.config import REACTPY_DEBUG
from reactpy.core._life_cycle_hook import HOOK_STACK
from reactpy.types import BaseLayout, LayoutEventMessage, LayoutUpdateMessage

logger = getLogger(__name__)


SendCoroutine = Callable[[LayoutUpdateMessage | dict[str, Any]], Awaitable[None]]
"""Send model patches given by a dispatcher"""

RecvCoroutine = Callable[[], Awaitable[LayoutEventMessage | dict[str, Any]]]
"""Called by a dispatcher to return a :class:`reactpy.core.layout.LayoutEventMessage`

The event will then trigger an :class:`reactpy.core.proto.EventHandlerType` in a layout.
"""


async def serve_layout(
    layout: BaseLayout[
        LayoutUpdateMessage | dict[str, Any], LayoutEventMessage | dict[str, Any]
    ],
    send: SendCoroutine,
    recv: RecvCoroutine,
) -> None:
    """Run a dispatch loop for a single view instance"""
    async with layout:
        async with create_task_group() as task_group:
            task_group.start_soon(_single_outgoing_loop, layout, send)
            task_group.start_soon(_single_incoming_loop, task_group, layout, recv)


async def _single_outgoing_loop(
    layout: BaseLayout[
        LayoutUpdateMessage | dict[str, Any], LayoutEventMessage | dict[str, Any]
    ],
    send: SendCoroutine,
) -> None:
    while True:
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


async def _single_incoming_loop(
    task_group: TaskGroup,
    layout: BaseLayout[
        LayoutUpdateMessage | dict[str, Any], LayoutEventMessage | dict[str, Any]
    ],
    recv: RecvCoroutine,
) -> None:
    while True:
        # We need to fire and forget here so that we avoid waiting on the completion
        # of this event handler before receiving and running the next one.
        task_group.start_soon(layout.deliver, await recv())
