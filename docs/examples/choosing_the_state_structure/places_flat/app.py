"""Flat state: the same leaf update touches one entry, and no ancestor rebuild."""

from data import PLACES

from reactpy import component, html, use_state


# start
def bind_visit(on_visit, place_id):
    # Handlers are called with the event alone, so the id is bound by a closure
    # rather than a lambda default — a handler has to be a coroutine, and a
    # coroutine cannot be a lambda. The default stays overridable so a parent's
    # bound handler can be re-bound for a deeper child.
    async def visit(event, target_id=place_id):
        await on_visit(event, target_id)

    return visit


@component
def place_tree(place_id, on_visit, visited):
    place = PLACES[place_id]
    children = place["childIds"]
    return html.li(
        {"key": place_id},
        place["title"],
        html.button(
            {"onClick": on_visit}, "Visited" if place_id in visited else "Visit"
        ),
        (
            html.ol(
                [
                    place_tree(child_id, bind_visit(on_visit, child_id), visited)
                    for child_id in children
                ]
            )
            if children
            else None
        ),
    )


@component
def travel_plan():
    # One dict keyed by id, plus one set of visited ids. Marking a place visited
    # touches exactly one entry — there is no enclosing object to rebuild.
    visited, set_visited = use_state(set())

    async def toggle(event, place_id=0):
        if place_id not in visited:
            set_visited({*visited, place_id})

    return html.div(
        html.h2("Places to visit"),
        html.ol(
            [
                place_tree(place_id, bind_visit(toggle, place_id), visited)
                for place_id in PLACES[0]["childIds"]
            ]
        ),
    )


@component
def app():
    return travel_plan()
