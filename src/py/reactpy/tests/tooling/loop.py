import asyncio
import threading
import time
from asyncio import wait_for
from collections.abc import Iterator
from contextlib import contextmanager

from reactpy.config import REACTPY_TESTING_DEFAULT_TIMEOUT


@contextmanager
def open_event_loop(as_current: bool = True) -> Iterator[asyncio.AbstractEventLoop]:
    """Open a new event loop and cleanly stop it

    Args:
        as_current: whether to make this loop the current loop in this thread
    """
    loop = asyncio.new_event_loop()
    try:
        if as_current:
            asyncio.set_event_loop(loop)
        loop.set_debug(True)
        yield loop
    finally:
        try:
            _cancel_all_tasks(loop, as_current)
            if as_current:
                loop.run_until_complete(
                    wait_for(
                        loop.shutdown_asyncgens(),
                        REACTPY_TESTING_DEFAULT_TIMEOUT.current,
                    )
                )
                loop.run_until_complete(
                    wait_for(
                        loop.shutdown_default_executor(),
                        REACTPY_TESTING_DEFAULT_TIMEOUT.current,
                    )
                )
        finally:
            if as_current:
                asyncio.set_event_loop(None)
            start = time.time()
            while loop.is_running():
                if (time.time() - start) > REACTPY_TESTING_DEFAULT_TIMEOUT.current:
                    msg = f"Failed to stop loop after {REACTPY_TESTING_DEFAULT_TIMEOUT.current} seconds"
                    raise TimeoutError(msg)
                time.sleep(0.1)
            loop.close()


def _cancel_all_tasks(loop: asyncio.AbstractEventLoop, is_current: bool) -> None:
    to_cancel = asyncio.all_tasks(loop)
    if not to_cancel:
        return

    done = threading.Event()
    count = len(to_cancel)

    def one_task_finished(future):
        nonlocal count
        count -= 1
        if count == 0:
            done.set()

    for task in to_cancel:
        loop.call_soon_threadsafe(task.cancel)
        task.add_done_callback(one_task_finished)

    if is_current:
        loop.run_until_complete(
            wait_for(
                asyncio.gather(*to_cancel, return_exceptions=True),
                REACTPY_TESTING_DEFAULT_TIMEOUT.current,
            )
        )
    elif not done.wait(timeout=3):  # user was responsible for cancelling all tasks
        msg = "Could not stop event loop in time"
        raise TimeoutError(msg)

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
