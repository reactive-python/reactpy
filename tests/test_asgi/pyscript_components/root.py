from reactpy import component, hooks, html


@component
def root():
    count, set_count = hooks.use_state(0)

    def increment(event):
        set_count(count + 1)

    return html.div(
        html.button(
            {"onClick": increment, "id": "incr", "data-count": count}, "Increment"
        ),
        html.p(f"PyScript Count: {count}"),
    )
