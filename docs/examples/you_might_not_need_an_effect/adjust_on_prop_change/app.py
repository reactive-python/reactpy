"""Adjust selection when the items change — by deriving, not by an Effect."""

from reactpy import component, html, use_state


# start
@component
def list_box(items):
    is_reverse, set_is_reverse = use_state(False)
    # One state value that remembers which list the choice belonged to. The
    # selection is *derived*: if the items changed, the old choice is not
    # valid for the new list, so it reads back as None. No Effect, no
    # intermediate render with a stale selection.
    chosen, set_chosen = use_state({"items": None, "value": None})
    selection = chosen["value"] if chosen["items"] == items else None

    shown = items[::-1] if is_reverse else items

    async def handle_is_reverse_click(event):
        set_is_reverse(not is_reverse)

    async def handle_chosen_click(event):
        set_chosen({"items": items, "value": shown[0]})

    return html.div(
        html.p(f"items: {shown}  selected: {selection}"),
        html.button({"onClick": handle_is_reverse_click}, "Reverse"),
        html.button(
            {"onClick": handle_chosen_click},
            "Select",
        ),
    )


@component
def app():
    items, set_items = use_state(["a", "b", "c"])

    async def handle_items_click(event):
        set_items([*items, f"item {len(items) + 1}"])

    return html.div(
        html.button(
            {"onClick": handle_items_click},
            "Add item",
        ),
        list_box(items),
    )
