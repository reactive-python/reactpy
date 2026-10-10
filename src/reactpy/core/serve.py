from __future__ import annotations

from collections.abc import Awaitable, Callable
from logging import getLogger
from typing import Any

from anyio import create_task_group
from anyio.abc import TaskGroup

from reactpy.config import REACTPY_DEBUG
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
    # Let the layout reach back into the browser for the properties and methods of the
    # events its handlers are working on. Older layouts simply do not have this hook.
    set_event_proxy_sender = getattr(layout, "set_event_proxy_sender", None)
    if callable(set_event_proxy_sender):
        set_event_proxy_sender(_send_through(send))

    async with layout:
        async with create_task_group() as task_group:
            task_group.start_soon(_single_outgoing_loop, layout, send)
            task_group.start_soon(_single_incoming_loop, task_group, layout, recv)


def _send_through(send: SendCoroutine) -> SendCoroutine:
    """Adapt the layout's outgoing message sender for live event requests"""

    async def send_event_proxy_request(
        message: LayoutUpdateMessage | dict[str, Any],
    ) -> None:
        await send(message)

    return send_event_proxy_request


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
