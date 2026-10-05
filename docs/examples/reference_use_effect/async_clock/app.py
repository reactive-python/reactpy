# start
import asyncio
from datetime import datetime, timezone

from reactpy import component, html, use_async_effect, use_state


@component
def clock():
    now, set_now = use_state(datetime.now(timezone.utc))

    async def effect():
        # Zero arguments. A long-running effect loops and honours cancellation.
        while True:
            set_now(datetime.now(timezone.utc))
            try:
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                break

    use_async_effect(effect)

    return html.h1(now.strftime("%H:%M:%S"))
