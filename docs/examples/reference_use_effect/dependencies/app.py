from data import ticker

from reactpy import component, html, use_effect, use_state

# start


@component
def live_feed():
    topic, set_topic = use_state("news")
    latest, set_latest = use_state("")

    def effect():
        # Re-runs whenever `topic` changes; the returned clean-up unsubscribes
        # the previous topic first, so you never keep two subscriptions.
        unsubscribe = ticker.subscribe(topic, set_latest)
        return unsubscribe

    use_effect(effect, dependencies=[topic])

    async def handle_topic_click(event):
        set_topic("sports" if topic == "news" else "news")

    async def handle_click(event):
        ticker.publish(topic, "ping")

    return html.div(
        html.p(f"Subscribed to: {topic}"),
        html.p(latest or "(nothing yet)"),
        html.button(
            {"onClick": handle_topic_click},
            "Switch topic",
        ),
        html.button({"onClick": handle_click}, "Publish"),
    )
