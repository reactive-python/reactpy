"""Reading state only to calculate the next state does not make it a
dependency: the functional updater removes it. Listing it instead would make
this Effect re-run itself.
"""

from reactpy import component, html, use_effect, use_state


# start
@component
def log_viewer(topic):
    lines, set_lines = use_state([])
    visible, set_visible = use_state(3)

    def record():
        # `lines` is only used to build the next value, so it is not a
        # dependency — and listing it would make this Effect re-trigger itself
        def append(current):
            return [*current, f"opened {topic}"]

        set_lines(append)

    use_effect(record, dependencies=[topic])

    async def handle_visible_click(e):
        set_visible(visible + 1)

    return html.div(
        html.button({"onClick": handle_visible_click}, f"Show {visible}"),
        html.ul([html.li({"key": i}, line) for i, line in enumerate(lines[-visible:])]),
    )


@component
def app():
    topic, set_topic = use_state("news")

    async def handle_topic_click(e):
        set_topic(topic + "x")

    return html.div(
        html.button({"onClick": handle_topic_click}, f"Topic {topic}"),
        log_viewer(topic),
    )
