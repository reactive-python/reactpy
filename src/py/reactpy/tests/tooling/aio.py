from asyncio import Event as _Event
from asyncio import wait_for

from reactpy.config import REACTPY_TESTING_DEFAULT_TIMEOUT


class Event(_Event):
    """An event with a ``wait_for`` method."""

    async def wait(self, timeout: float | None = None):
        return await wait_for(
            super().wait(),
            timeout=timeout or REACTPY_TESTING_DEFAULT_TIMEOUT.current,
        )
