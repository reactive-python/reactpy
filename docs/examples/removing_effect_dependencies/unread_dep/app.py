"""An Effect that writes a summary into state, but lists only one of the values
it reads. The summary keeps describing an older render and nothing warns you.
"""

from reactpy import component, html, use_effect, use_state


# start
@component
def reporter(topic):
    count, set_count = use_state(0)
    theme, set_theme = use_state("light")
    summary, set_summary = use_state("no report yet")

    def report():
        # reads `count` and `theme`, but neither is in the dependency list
        set_summary(f"topic={topic} count={count} theme={theme}")
        print(f"report topic={topic} count={count} theme={theme}")

    use_effect(report, dependencies=[topic])

    return html.div(
        html.button({"onClick": lambda e: set_count(count + 1)}, f"Count {count}"),
        html.button(
            {"onClick": lambda e: set_theme("dark" if theme == "light" else "light")},
            f"Theme {theme}",
        ),
        html.p(f"live: count={count} theme={theme}"),
        html.p(f"summary: {summary}"),
    )


@component
def app():
    topic, set_topic = use_state("news")
    return html.div(
        html.button({"onClick": lambda e: set_topic(topic + "x")}, f"Topic {topic}"),
        reporter(topic),
    )
