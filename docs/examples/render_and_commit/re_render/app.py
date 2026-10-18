import asyncio
from datetime import UTC, datetime

from reactpy import component, html, use_async_effect, use_state


# start
@component
def clock():
    now, set_now = use_state(datetime.now(UTC))

    async def tick():
        while True:
            await asyncio.sleep(1)
            set_now(datetime.now(UTC))

    use_async_effect(tick, dependencies=[])

    return html.h1(now.strftime("%H:%M:%S"))
