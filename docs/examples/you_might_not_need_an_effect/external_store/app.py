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

    return html.div(
        html.button({"onClick": lambda event: clock.tick()}, "Tick"),
        html.button(
            {"onClick": lambda event: set_watching(not watching)},
            "Stop watching" if watching else "Watch",
        ),
        *([] if not watching else [clock_view()]),
    )


# end
