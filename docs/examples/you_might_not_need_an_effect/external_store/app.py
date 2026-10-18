"""The legitimate use of an Effect: mirror a value that lives outside ReactPy."""

from data import clock

from reactpy import component, html, use_effect, use_state


# start
@component
def clock_view():
    # The value is owned by `clock`, not by this component, so it cannot be
    # derived during render -- ReactPy has to be told when it changes.
    ticks, set_ticks = use_state(clock.get())

    def effect():
        # Subscribe, and hand back the unsubscribe. This is what an Effect
        # is for: the source of truth lives outside ReactPy.
        def on_change():
            set_ticks(clock.get())

        return clock.subscribe(on_change)

    use_effect(effect, dependencies=[])

    return html.div(html.h1(f"{ticks} ticks"))


@component
def app():
    watching, set_watching = use_state(True)

    async def handle_click(event):
        clock.tick()

    async def handle_watching_click(event):
        set_watching(not watching)

    return html.div(
        html.button({"onClick": handle_click}, "Tick"),
        html.button(
            {"onClick": handle_watching_click},
            "Stop watching" if watching else "Watch",
        ),
        *([] if not watching else [clock_view()]),
    )
