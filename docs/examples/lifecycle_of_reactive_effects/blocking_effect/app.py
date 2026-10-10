"""A sync Effect blocks the connection's event loop, like any sync work."""

import time

from reactpy import component, html, use_effect, use_state


# start
@component
def preview():
    width, set_width = use_state(100)

    def effect():
        # Stands in for image encoding, a model call, a blocking driver.
        # Effects run on the connection's own event loop, so while this runs
        # nothing else on the connection can: no other render, no other
        # handler. Only the browser's local typing stays responsive.
        started = time.perf_counter()
        time.sleep(0.4)
        print(f"effect held the loop for {time.perf_counter() - started:.2f}s")

    use_effect(effect, dependencies=[width])

    return html.div(
        html.h1(f"width {width}"),
        html.button({"onClick": lambda event: set_width(width + 1)}, "Wider"),
    )


# end
