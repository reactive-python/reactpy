import idom


@idom.component
def DivInDiv():
    stop_propagatation, set_stop_propagatation = idom.hooks.use_state(True)
    inner_count, set_inner_count = idom.hooks.use_state(0)
    outer_count, set_outer_count = idom.hooks.use_state(0)

    div_in_div = idom.html.div(
        {
            "onClick": idom.event(lambda e: set_outer_count(outer_count + 1)),
            "style": {"height": "100px", "width": "100px", "backgroundColor": "red"},
        },
        idom.html.div(
            {
                "onClick": idom.event(
                    lambda e: set_inner_count(inner_count + 1),
                    stop_propagation=stop_propagatation,
                ),
                "style": {"height": "50px", "width": "50px", "backgroundColor": "blue"},
            },
        ),
    )

    return idom.html.div(
        idom.html.button(
            {"onClick": lambda e: set_stop_propagatation(not stop_propagatation)},
            "Toggle Propogation",
        ),
        idom.html.pre(f"Will propagate: {not stop_propagatation}"),
        idom.html.pre(f"Inner click count: {inner_count}"),
        idom.html.pre(f"Outer click count: {outer_count}"),
        div_in_div,
    )


idom.run(DivInDiv)
