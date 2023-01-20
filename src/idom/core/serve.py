from __future__ import annotations

from asyncio import create_task
from logging import getLogger
from typing import Awaitable, Callable

from anyio import create_task_group

from idom.core.types import LayoutEventMessage, LayoutType, LayoutUpdateMessage


logger = getLogger(__name__)


SendCoroutine = Callable[[LayoutUpdateMessage], Awaitable[None]]
"""Send model patches given by a dispatcher"""

RecvCoroutine = Callable[[], Awaitable[LayoutEventMessage]]
"""Called by a dispatcher to return a :class:`idom.core.layout.LayoutEventMessage`

The event will then trigger an :class:`idom.core.proto.EventHandlerType` in a layout.
"""


class Stop(BaseException):
    """Stop serving changes and events

    Raising this error will tell dispatchers to gracefully exit. Typically this is
    called by code running inside a layout to tell it to stop rendering.
    """


async def serve_layout(
    layout: LayoutType[LayoutUpdateMessage, LayoutEventMessage],
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
            logger.info(f"Stopped serving {layout}")


async def _single_outgoing_loop(
    layout: LayoutType[LayoutUpdateMessage, LayoutEventMessage], send: SendCoroutine
) -> None:
    while True:
        await send(await layout.render())


async def _single_incoming_loop(
    layout: LayoutType[LayoutUpdateMessage, LayoutEventMessage], recv: RecvCoroutine
) -> None:
    while True:
        # We need to fire and forget here so that we avoid waiting on the completion
        # of this event handler before receiving and running the next one.
        create_task(layout.deliver(await recv()))
