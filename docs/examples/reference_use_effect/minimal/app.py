from data import ticker

from reactpy import component, html, use_effect, use_state

# start


@component
def live_feed():
    latest, set_latest = use_state("waiting for a message...")

    def effect():
        # Runs once on mount; the returned function runs on unmount.
        unsubscribe = ticker.subscribe("news", set_latest)
        return unsubscribe

    use_effect(effect, dependencies=[])

    async def handle_click(event):
        ticker.publish("news", "Hello!")

    return html.div(
        html.h1(latest),
        html.button(
            {"onClick": handle_click},
            "Publish",
        ),
    )
