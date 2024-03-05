from __future__ import annotations

import random
import string
from collections.abc import Awaitable
from logging import getLogger
from typing import Callable
from warnings import warn

from anyio import create_task_group
from anyio.abc import TaskGroup

from reactpy.backend.hooks import ConnectionContext
from reactpy.backend.types import Connection
from reactpy.config import REACTPY_DEBUG_MODE
from reactpy.core._life_cycle_hook import clear_hook_state, create_hook_state
from reactpy.core.layout import Layout
from reactpy.core.state_recovery import StateRecoveryFailureError, StateRecoveryManager
from reactpy.core.types import (
    ClientStateMessage,
    IsReadyMessage,
    LayoutEventMessage,
    LayoutType,
    LayoutUpdateMessage,
    ReconnectingCheckMessage,
    RootComponentConstructor,
)

logger = getLogger(__name__)


SendCoroutine = Callable[
    [
        LayoutUpdateMessage
        | ReconnectingCheckMessage
        | IsReadyMessage
        | ClientStateMessage
    ],
    Awaitable[None],
]
"""Send model patches given by a dispatcher"""

RecvCoroutine = Callable[
    [], Awaitable[LayoutEventMessage | ReconnectingCheckMessage | ClientStateMessage]
]
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
    layout: LayoutType[LayoutUpdateMessage, LayoutEventMessage],
    send: SendCoroutine,
    recv: RecvCoroutine,
) -> None:
    """Run a dispatch loop for a single view instance"""

    try:
        async with create_task_group() as task_group:
            task_group.start_soon(_single_outgoing_loop, layout, send)
            task_group.start_soon(_single_incoming_loop, task_group, layout, recv, send)
    except Stop:  # nocov
        warn(
            "The Stop exception is deprecated and will be removed in a future version",
            UserWarning,
            stacklevel=1,
        )
        logger.info(f"Stopped serving {layout}")


async def _single_outgoing_loop(
    layout: LayoutType[LayoutUpdateMessage, LayoutEventMessage], send: SendCoroutine
) -> None:
    while True:
        token = create_hook_state()
        try:
            update = await layout.render()
            try:
                await send(update)
            except Exception:  # nocov
                if not REACTPY_DEBUG_MODE.current:
                    msg = (
                        "Failed to send update. More info may be available "
                        "if you enabling debug mode by setting "
                        "`reactpy.config.REACTPY_DEBUG_MODE.current = True`."
                    )
                    logger.error(msg)
                raise
        finally:
            clear_hook_state(token)


async def _single_incoming_loop(
    task_group: TaskGroup,
    layout: LayoutType[LayoutUpdateMessage, LayoutEventMessage],
    recv: RecvCoroutine,
    send: SendCoroutine,
) -> None:
    while True:
        # We need to fire and forget here so that we avoid waiting on the completion
        # of this event handler before receiving and running the next one.
        task_group.start_soon(layout.deliver, await recv())


class WebsocketServer:
    def __init__(
        self,
        send: SendCoroutine,
        recv: RecvCoroutine,
        state_recovery_manager: StateRecoveryManager | None = None,
    ) -> None:
        self._send = send
        self._recv = recv
        self._state_recovery_manager = state_recovery_manager
        self._salt: str | None = None

    async def handle_connection(
        self, connection: Connection, constructor: RootComponentConstructor
    ):
        layout = Layout(
            ConnectionContext(
                constructor(),
                value=connection,
            ),
        )
        async with layout:
            await self._handshake(layout)
            # salt may be set to client's old salt during handshake
            if self._state_recovery_manager:
                layout.set_recovery_serializer(
                    self._state_recovery_manager.create_serializer(self._salt)
                )
            await serve_layout(
                layout,
                self._send,
                self._recv,
            )

    async def _handshake(self, layout: Layout) -> None:
        await self._send(ReconnectingCheckMessage(type="reconnecting-check"))
        result = await self._recv()
        self._salt = "".join(random.choices(string.ascii_letters + string.digits, k=8))
        if result["type"] == "reconnecting-check":
            if result["value"] == "yes":
                if self._state_recovery_manager is None:
                    logger.warning(
                        "Reconnection detected, but no state recovery manager provided"
                    )
                    layout.start_rendering()
                else:
                    logger.info("Handshake: Doing state rebuild for reconnection")
                    self._salt = await self._do_state_rebuild_for_reconnection(layout)
                    logger.info("Handshake: Completed doing state rebuild")
            else:
                logger.info("Handshake: new connection")
                layout.start_rendering()
        else:
            logger.warning(
                f"Unexpected type when expecting reconnecting-check: {result['type']}"
            )
        await self._indicate_ready(),

    async def _indicate_ready(self) -> None:
        await self._send(IsReadyMessage(type="is-ready", salt=self._salt))

    async def _do_state_rebuild_for_reconnection(self, layout: Layout) -> str:
        salt = self._salt
        await self._send(ClientStateMessage(type="client-state"))
        client_state_msg = await self._recv()
        if client_state_msg["type"] != "client-state":
            logger.warning(
                f"Unexpected type when expecting client-state: {client_state_msg['type']}"
            )
            return
        state_vars = client_state_msg["value"]
        try:
            serializer = self._state_recovery_manager.create_serializer(
                client_state_msg["salt"]
            )
            client_state = serializer.deserialize_client_state(state_vars)
            layout.reconnecting.set_current(True)
            layout.client_state = client_state
        except StateRecoveryFailureError:
            logger.exception("State recovery failed")
            layout.reconnecting.set_current(False)
            layout.client_state = {}
        else:
            salt = client_state_msg["salt"]
        try:
            layout.start_rendering_for_reconnect()
            await layout.render_until_queue_empty()
        except StateRecoveryFailureError:
            logger.warning("Client state non-recoverable. Starting fresh")
            await layout.finish()
            await layout.start()
            layout.start_rendering()
        layout.reconnecting.set_current(False)
        layout.client_state = {}
        return salt
