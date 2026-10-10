"""Subscribe on mount, unsubscribe on unmount, and never leak a subscriber."""

from data import ticker

from reactpy import component, html, use_effect, use_state


# start
@component
def scroll_log(topic):
    lines, set_lines = use_state([])

    def effect():
        # The clean-up is what keeps the subscriber count at 1 across
        # re-subscriptions. Forget it and every render adds another callback.
        def on_message(message):
            set_lines(lambda previous: [*previous, message])

        unsubscribe = ticker.subscribe(topic, on_message)
        return unsubscribe

    use_effect(effect, dependencies=[topic])

    return html.div(
        html.h2(topic),
        html.ul([html.li({"key": index}, line) for index, line in enumerate(lines)]),
    )


@component
def app():
    topic, set_topic = use_state("news")
    watching, set_watching = use_state(True)

    return html.div(
        html.button(
            {
                "onClick": lambda event: set_topic(
                    "sports" if topic == "news" else "news"
                )
            },
            "Switch topic",
        ),
        html.button(
            {"onClick": lambda event: set_watching(not watching)},
            "Stop watching" if watching else "Watch",
        ),
        html.button({"onClick": lambda event: ticker.publish(topic, "ping")}, "Ping"),
        *([] if not watching else [scroll_log(topic)]),
    )
