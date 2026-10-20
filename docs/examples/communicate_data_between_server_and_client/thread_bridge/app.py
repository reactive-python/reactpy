"""Run blocking code off the event loop and update state when it lands."""

import asyncio
import time

from reactpy import component, html, use_async_effect, use_state


# start
def blocking_render(width):
    """A synchronous, CPU-bound library call. Never run this on the loop."""
    time.sleep(0.4)  # stands in for image encoding, model inference, ...
    return f"rendered {width}px"


@component
def preview(width):
    result, set_result = use_state("rendering...")

    async def render():
        # to_thread keeps the loop free; the setter runs back on the loop.
        set_result(await asyncio.to_thread(blocking_render, width))

    use_async_effect(render, dependencies=[width])

    return html.h1(result)


# end
