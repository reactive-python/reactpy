"""Poll an outside value and push it into the view declaratively."""

import asyncio

from reactpy import component, html, use_async_effect, use_state


# start
async def fetch_price(symbol):
    """Stand-in for a request to an exchange, a sensor, a queue."""
    await asyncio.sleep(1)
    return f"{symbol}: 42.10"


@component
def ticker(symbol):
    price, set_price = use_state("loading...")

    async def poll():
        while True:
            try:
                set_price(await fetch_price(symbol))
            except Exception as error:
                set_price(f"error: {error}")
            try:
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                break

    use_async_effect(poll)

    return html.div(html.h1(price))


# end
