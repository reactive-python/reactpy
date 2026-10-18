from reactpy import component, html, use_state

# start


@component
def counter():
    count, set_count = use_state(0)

    # Nothing outside this component is touched. `count` comes from use_state,
    # which ReactPy keeps per component instance -- so two connections to this
    # same component each have their own number, and re-running the render
    # changes nothing but the value returned.
    async def handle_count_click(event):
        set_count(count + 1)

    return html.div(
        html.h1(count),
        html.button({"onClick": handle_count_click}, "Add 1"),
    )
