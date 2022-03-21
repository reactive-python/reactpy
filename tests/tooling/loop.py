import asyncio
from asyncio import wait_for
from contextlib import contextmanager
from typing import Iterator


TIMEOUT = 3


@contextmanager
def open_event_loop() -> Iterator[asyncio.AbstractEventLoop]:
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        loop.set_debug(True)
        yield loop
    finally:
        try:
            _cancel_all_tasks(loop)
            loop.run_until_complete(wait_for(loop.shutdown_asyncgens(), TIMEOUT))
            loop.run_until_complete(wait_for(loop.shutdown_default_executor(), TIMEOUT))
        finally:
            asyncio.set_event_loop(None)
            loop.close()


def _cancel_all_tasks(loop: asyncio.AbstractEventLoop) -> None:
    to_cancel = asyncio.all_tasks(loop)
    if not to_cancel:
        return

    for task in to_cancel:
        task.cancel()

    loop.run_until_complete(
        wait_for(asyncio.gather(*to_cancel, loop=loop, return_exceptions=True), TIMEOUT)
    )

    for task in to_cancel:
        if task.cancelled():
            continue
        if task.exception() is not None:
            loop.call_exception_handler(
                {
                    "message": "unhandled exception during event loop shutdown",
                    "exception": task.exception(),
                    "task": task,
                }
            )
