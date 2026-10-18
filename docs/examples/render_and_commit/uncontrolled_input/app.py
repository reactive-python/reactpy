from reactpy import component, html, use_state


# start
@component
def app():
    count, set_count = use_state(0)

    async def handle_count_click(event):
        set_count(count + 1)

    return html.div(
        html.button({"onClick": handle_count_click}, "Re-render"),
        html.p(f"Rendered {count} times"),
        # No `value`: the browser owns this field, so ReactPy never rewrites it.
        html.input({"placeholder": "Type here and then click the button"}),
    )
