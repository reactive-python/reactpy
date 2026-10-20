"""Deeply nested state: one leaf update must rebuild every ancestor."""

from data import INITIAL_PLAN

from reactpy import component, html, use_state


# start
def mark_visited(node, target_id):
    """Copy this node, and recurse — the whole tree is rebuilt top-down."""
    if node["id"] == target_id:
        return {**node, "visited": True}
    return {
        **node,
        "childPlaces": [
            mark_visited(child, target_id) for child in node["childPlaces"]
        ],
    }


@component
def place_tree(place, on_visit):
    children = place["childPlaces"]
    return html.li(
        {"key": place["id"]},
        place["title"],
        html.button(
            {"onClick": on_visit}, "Visited" if place.get("visited") else "Visit"
        ),
        (
            html.ol([place_tree(child, on_visit) for child in children])
            if children
            else None
        ),
    )


@component
def travel_plan():
    plan, set_plan = use_state(INITIAL_PLAN)

    def make_visit(place_id):
        # A factory, because a handler has to be a coroutine and a coroutine
        # cannot be a lambda — this is how the id gets bound instead.
        async def visit(event):
            set_plan(mark_visited(plan, place_id))

        return visit

    return html.div(
        html.h2("Places to visit"),
        html.ol(
            [
                place_tree(place, make_visit(place["id"]))
                for place in plan["childPlaces"]
            ]
        ),
    )


@component
def app():
    return travel_plan()
