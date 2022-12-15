from __future__ import annotations

from asyncio import (
    FIRST_COMPLETED,
    Event,
    Queue,
    Semaphore,
    Task,
    create_task,
    sleep,
    wait,
)
from contextlib import AsyncExitStack
from dataclasses import dataclass
from logging import getLogger
from typing import AsyncIterator
from weakref import ReferenceType, finalize, ref

from idom.backend.common.types import ByteStream, FileUploadMessage


logger = getLogger(__name__)


class ByteStreamFiles:
    def __init__(
        self,
        max_chunk_size: int | None = None,
        max_queue_size: int | None = None,
        max_stream_count: int | None = None,
        message_timeout: float | None = None,
        completion_timeout: float | None = None,
    ) -> None:
        self._max_chunk_size = max_chunk_size
        self._max_queue_size = max_queue_size
        self._message_timeout = message_timeout
        self._completion_timeout = completion_timeout
        self._stream_count_semaphore = (
            Semaphore(max_stream_count) if max_stream_count else None
        )
        self._streams: dict[str, _ByteStreamState] = {}

    def get(self, file: str) -> ByteStream:
        """Get a byte stream that will be written to."""
        if file not in self._streams:
            stream = ByteStream(
                self._max_chunk_size,
                self._max_queue_size,
                self._message_timeout,
            )
            self._create_stream_state(stream)
        else:
            stream = self._streams[file]
        return stream

    async def handle(self, message: FileUploadMessage) -> None:
        file = message["file"]
        state = self._streams.get(file)
        if state is None:
            logger.info(f"No stream exists for {file!r}")

        stream = state.stream()
        if stream is None:
            logger.info(f"No stream exists for {file!r}")

        if self._stream_count_semaphore is not None:
            await state.exit_stack.enter_async_context(self._stream_count_semaphore)

        await stream.put(message["data"])

        if not message["bytes-remaining"]:
            await self._clean_stream_state(file)

    def _create_stream_state(self, file: str, stream: ByteStream) -> None:
        async def clean_on_timeout():
            await sleep(self._completion_timeout)
            logger.warning(
                f"File upload for {file!r} timed out "
                f"after {self._completion_timeout} seconds."
            )
            await self._clean_stream_state(file)

        self._streams[file] = _ByteStreamState(
            stream=ref(stream),
            exit_stack=AsyncExitStack(),
            timeout_task=create_task(clean_on_timeout()),
        )

        finalize(stream, lambda: create_task(self._create_stream_state(file)))

    async def _clean_stream_state(self, file: str) -> None:
        state = self._streams.pop(file, None)
        if state is None:
            return None
        state.timeout_task.cancel()
        await self._streams.pop(file).exit_stack.aclose()


@dataclass
class _ByteStreamState:
    stream: ReferenceType[ByteStream]
    exit_stack: AsyncExitStack
    timeout_task: Task[None]


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
        """Put data into the stream and raise ``RuntimeError`` if closed."""
        if self._closed.is_set():
            raise RuntimeError("Stream already closed.")
        elif self._max_chunk_size and len(data) > self._max_chunk_size:
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
            return None
        elif closed_task.done():
            raise RuntimeError("Stream closed while putting.")
        else:
            raise TimeoutError(f"No data after {timeout} seconds")

    async def get(self, timeout: float | None = None) -> bytes | None:
        """Return bytes or None when the stream is closed."""
        if self._closed.is_set():
            return None

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
        """Close the stream"""
        self._closed.set()

    def is_closed(self):
        """Whether this stream is already closed"""
        return self._closed
