from __future__ import annotations

from asyncio import create_task
from logging import getLogger
from typing import Any, Awaitable, Callable

from anyio import create_task_group

from idom.core.layout import LayoutEvent, LayoutUpdate
from idom.core.server.types import (
    ClientInfoMessage,
    ClientMessage,
    FileHandler,
    FileUploadMessage,
    LayoutEventMessage,
    ServerMessage,
)
from idom.core.types import LayoutType


logger = getLogger(__name__)
VERSION = "0.0.1"

SendCoroutine = Callable[[ServerMessage], Awaitable[None]]
RecvCoroutine = Callable[[], Awaitable[ClientMessage]]
BuiltinLayout = LayoutType[LayoutUpdate, LayoutEvent]


async def serve(
    send: SendCoroutine,
    recv: RecvCoroutine,
    layout: BuiltinLayout,
    file_handler: FileHandler | None = None,
) -> None:

    async with layout:
        try:
            async with create_task_group() as task_group:
                task_group.start_soon(_outgoing_loop, send, layout)
                task_group.start_soon(_incoming_loop, recv, layout, file_handler)
        except Stop:
            logger.info("Stopped dispatch task")


class Stop(BaseException):
    """Stop serving changes and events

    Raising this error will tell dispatchers to gracefully exit. Typically this is
    called by code running inside a layout to tell it to stop rendering.
    """


async def _outgoing_loop(send: SendCoroutine, layout: BuiltinLayout) -> None:
    await send({"type": "server-info", "version": VERSION})
    while True:
        await send({"type": "layout-update", "data": await layout.render()})


async def _incoming_loop(
    recv: RecvCoroutine,
    layout: BuiltinLayout,
    file_handler: FileHandler | None,
) -> None:
    async def handle_layout_event(message: LayoutEventMessage) -> None:
        await layout.deliver(message["data"])

    async def handle_client_info(message: ClientInfoMessage) -> None:
        ...

    async def handle_file_upload(message: FileUploadMessage) -> None:
        if file_handler:
            await file_handler.handle(message)

    message_handlers: dict[str, Callable[[Any], Awaitable[None]]] = {
        "layout-event": handle_layout_event,
        "client-info": handle_client_info,
        "file-upload": handle_file_upload,
    }

    while True:
        message = await recv()
        handler = message_handlers.get(message["type"])
        if handler is None:
            logger.error(f"Unknown message type {message['type']!r}")
        # We need to fire and forget here so that we avoid waiting on the completion
        # of this event handler before receiving and running the next one.
        create_task(handler(message))
