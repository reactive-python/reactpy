import asyncio
import time

from reactpy import Ref, component, html, use_async_effect, use_ref, use_state

# start


@component
def stopwatch():
    # What the UI renders lives in state. What only the handlers and the
    # ticking effect read -- and which must never trigger a render of its own
    # -- lives in a ref.
    elapsed, set_elapsed = use_state(0.0)
    running, set_running = use_state(False)
    started_at: Ref[float | None] = use_ref(None)

    async def tick():
        # The ref is the same object on every render, so this long-lived loop
        # always sees whatever the button handlers wrote into it.
        while started_at.current is not None:
            await asyncio.sleep(0.1)
            set_elapsed(time.monotonic() - started_at.current)

    use_async_effect(tick, dependencies=[running])

    async def start(event=None):
        started_at.current = time.monotonic()
        set_running(True)

    async def stop(event=None):
        if started_at.current is not None:
            # Write the exact final value; the ticking effect only samples
            # every 0.1s, so relying on it alone would leave the display
            # slightly behind.
            set_elapsed(time.monotonic() - started_at.current)
            started_at.current = None
        set_running(False)

    async def reset(event=None):
        started_at.current = None
        set_running(False)
        set_elapsed(0.0)

    return html.div(
        html.h1(f"{elapsed:.1f}s"),
        html.button(
            {"onClick": stop if running else start},
            "Stop" if running else "Start",
        ),
        html.button({"onClick": reset}, "Reset"),
    )
