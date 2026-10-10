"""Gating a subscription: pass it as a prop, do not delete the hook call."""

from reactpy import component, html, use_effect, use_state


# start
@component
def feed(topic, enabled):
    def effect():
        if not enabled:
            # Nothing to set up, and nothing to clean up. The hook call below
            # still happens, so the hook order never changes.
            return None

        print(f"subscribe {topic}")

        def cleanup():
            print(f"unsubscribe {topic}")

        return cleanup

    use_effect(effect, dependencies=[topic, enabled])

    return html.p(f"{topic}")


@component
def app():
    topic, set_topic = use_state("news")
    enabled, set_enabled = use_state(True)

    return html.div(
        html.button(
            {"onClick": lambda event: set_enabled(not enabled)},
            "Stop" if enabled else "Start",
        ),
        html.button(
            {
                "onClick": lambda event: set_topic(
                    "sports" if topic == "news" else "news"
                )
            },
            "Switch topic",
        ),
        feed(topic, enabled),
    )


# end
