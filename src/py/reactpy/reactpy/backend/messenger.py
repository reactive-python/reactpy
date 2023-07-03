from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable
from typing import Callable

from anyio import Event, create_memory_object_stream, create_task_group
from anyio.abc import ObjectReceiveStream, ObjectSendStream

from reactpy.core.types import Message

_MessageStream = tuple[ObjectSendStream[Message], ObjectReceiveStream[Message]]


class Messenger:
    """A messenger for sending and receiving messages"""

    def __init__(self) -> None:
        self._task_group = create_task_group()
        self._streams: dict[str, list[_MessageStream]] = {}
        self._recv_began: dict[str, Event] = {}

    def start_producer(self, producer: Callable[[], AsyncIterator[Message]]) -> None:
        """Add a message producer"""

        async def _producer() -> None:
            async for message in producer():
                await self.send(message)

        self._task_group.start_soon(_producer)

    def start_consumer(
        self, message_type: str, consumer: Callable[[Message], Awaitable[None]]
    ) -> None:
        """Add a message consumer"""

        async def _consumer() -> None:
            async for message in self.receive(message_type):
                self._task_group.start_soon(consumer, message)

        self._task_group.start_soon(_consumer)

    async def send(self, message: Message) -> None:
        """Send a message to all consumers of the message type"""
        for send, _ in self._streams.get(message["type"], []):
            await send.send(message)

    async def receive(self, message_type: str) -> AsyncIterator[Message]:
        """Receive messages of a given type"""
        send, recv = create_memory_object_stream()
        self._streams.setdefault(message_type, []).append((send, recv))
        async with recv:
            async with send:
                async for message in recv:
                    yield message

    async def __aenter__(self) -> Messenger:
        await self._task_group.__aenter__()
        return self

    async def __aexit__(self, *args) -> None:
        await self._task_group.__aexit__(*args)
