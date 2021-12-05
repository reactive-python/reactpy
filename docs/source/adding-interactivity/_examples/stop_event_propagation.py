from idom import component, event, hooks, html, run


@component
def DivInDiv():
    stop_propagatation, set_stop_propagatation = hooks.use_state(True)
    inner_count, set_inner_count = hooks.use_state(0)
    outer_count, set_outer_count = hooks.use_state(0)

    div_in_div = html.div(
        {
            "onClick": lambda event: set_outer_count(outer_count + 1),
            "style": {"height": "100px", "width": "100px", "backgroundColor": "red"},
        },
        html.div(
            {
                "onClick": event(
                    lambda event: set_inner_count(inner_count + 1),
                    stop_propagation=stop_propagatation,
                ),
                "style": {"height": "50px", "width": "50px", "backgroundColor": "blue"},
            },
        ),
    )

    return html.div(
        html.button(
            {"onClick": lambda event: set_stop_propagatation(not stop_propagatation)},
            "Toggle Propogation",
        ),
        html.pre(f"Will propagate: {not stop_propagatation}"),
        html.pre(f"Inner click count: {inner_count}"),
        html.pre(f"Outer click count: {outer_count}"),
        div_in_div,
    )


run(DivInDiv)
