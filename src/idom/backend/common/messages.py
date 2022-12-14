from asyncio import FIRST_COMPLETED, Event, Queue, create_task, wait
from typing import AsyncIterator

from idom.backend.common.types import (
    ByteStream,
    ClientMessageType,
    FileUploadMessage,
    ServerMessageType,
)


class MessageHandler:
    def __init__(self, send, recv):
        self._send = send
        self._recv = recv

    async def send(self, message: ServerMessageType) -> None:
        ...

    async def recv(self, message: ClientMessageType) -> None:
        ...


class FileUploadHandler:
    def __init__(
        self,
        max_chunk_size: int | None,
        max_queue_size: int | None,
        completion_timeout: float,
        message_timeout: float,
    ) -> None:
        self._max_chunk_size = max_chunk_size
        self._max_queue_size = max_queue_size
        self._streams: dict[str, ByteStream] = {}

    def get_stream(self, name: str, create_if_missing: bool = True) -> ByteStream:
        try:
            return self._streams[name]
        except KeyError:
            if not create_if_missing:
                raise

        stream = self._streams[name] = ByteStream(
            self._max_chunk_size, self._max_queue_size
        )
        return stream

    async def handle(self, message: FileUploadMessage) -> None:
        ...


class ByteStream:
    def __init__(
        self,
        max_chunk_size: int | None = None,
        max_queue_size: int | None = None,
        default_timeout: float | None = None,
    ) -> None:
        self._queue: Queue[bytes] = Queue(max_queue_size or 0)
        self._max_chunk_size = max_chunk_size
        self._closed = Event()
        self._default_timeout = default_timeout

    async def put(self, data: bytes, timeout: float) -> None:
        if self._max_chunk_size and len(data) > self._max_chunk_size:
            raise RuntimeError(f"Max chunk size of {self._max_chunk_size} exceeded")

        timeout = timeout if timeout is not None else self._default_timeout

        put_task = create_task(self._queue.put(data))
        closed_task = create_task(self._closed.wait())
        await wait(
            (put_task, closed_task),
            timeout=timeout,
            return_when=FIRST_COMPLETED,
        )

        if put_task.done():
            return await put_task.result()
        elif closed_task.done():
            return None
        else:
            raise TimeoutError(f"No data after {timeout} seconds")

    async def get(self, timeout: float | None = None) -> bytes | None:
        timeout = timeout if timeout is not None else self._default_timeout

        get_task = create_task(self._queue.get())
        closed_task = create_task(self._closed.wait())
        await wait(
            (get_task, closed_task),
            timeout=timeout,
            return_when=FIRST_COMPLETED,
        )

        if get_task.done():
            return await get_task.result()
        elif closed_task.done():
            return None
        else:
            raise TimeoutError(f"No data after {timeout} seconds")

    async def iter(self, timeout: float) -> AsyncIterator[bytes]:
        while True:
            value = await self.get(timeout)
            if value is None:
                return
            yield value

    def close(self) -> None:
        self._closed.set()

    def is_closed(self):
        return self._closed


class ClosedBytesStream(Exception):
    """Raised when an action is performed on a closed ByteStream"""
