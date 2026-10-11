from reactpy import component, event, hooks, html, run


@component
def DivInDiv():
    stop_propagatation, set_stop_propagatation = hooks.use_state(True)
    inner_count, set_inner_count = hooks.use_state(0)
    outer_count, set_outer_count = hooks.use_state(0)

    async def count_outer_click(event):
        set_outer_count(outer_count + 1)

    async def count_inner_click(event):
        set_inner_count(inner_count + 1)

    async def toggle_propagation(event):
        set_stop_propagatation(not stop_propagatation)

    div_in_div = html.div(
        {
            "on_click": count_outer_click,
            "style": {"height": "100px", "width": "100px", "background_color": "red"},
        },
        html.div(
            {
                "on_click": event(
                    count_inner_click,
                    stop_propagation=stop_propagatation,
                ),
                "style": {
                    "height": "50px",
                    "width": "50px",
                    "background_color": "blue",
                },
            }
        ),
    )

    return html.div(
        html.button({"on_click": toggle_propagation}, "Toggle Propagation"),
        html.pre(f"Will propagate: {not stop_propagatation}"),
        html.pre(f"Inner click count: {inner_count}"),
        html.pre(f"Outer click count: {outer_count}"),
        div_in_div,
    )


run(DivInDiv)
