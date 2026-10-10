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

    return html.div(
        html.p(f"items: {shown}  selected: {selection}"),
        html.button(
            {"onClick": lambda event: set_is_reverse(not is_reverse)}, "Reverse"
        ),
        html.button(
            {"onClick": lambda event: set_chosen({"items": items, "value": shown[0]})},
            "Select",
        ),
    )


@component
def app():
    items, set_items = use_state(["a", "b", "c"])

    return html.div(
        html.button(
            {"onClick": lambda event: set_items([*items, f"item {len(items) + 1}"])},
            "Add item",
        ),
        list_box(items),
    )


# end
