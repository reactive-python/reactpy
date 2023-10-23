from reactpy import component, html, run, use_state
from reactpy.core.types import State


@component
def Item(item: str, all_items: State[list[str]]):
    color = use_state(None)

    def deleteme(event):
        all_items.set_value([i for i in all_items.value if (i != item)])

    def colorize(event):
        color.set_value("blue" if not color.value else None)

    return html.div(
        {"id": item, "style": {"background_color": color.value}},
        html.button({"on_click": colorize}, f"Color {item}"),
        html.button({"on_click": deleteme}, f"Delete {item}"),
    )


@component
def App():
    items = use_state(["A", "B", "C"])
    return html._([Item(item, items, key=item) for item in items.value])


run(App)
