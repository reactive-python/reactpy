"""Flat state: the same leaf update touches one entry, and no ancestor rebuild."""

from data import PLACES

from reactpy import component, html, use_state


# start
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
                    place_tree(
                        child_id,
                        lambda event, cid=child_id: on_visit(event, cid),
                        visited,
                    )
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

    def toggle(event, place_id=0):
        if place_id not in visited:
            set_visited({*visited, place_id})

    return html.div(
        html.h2("Places to visit"),
        html.ol(
            [
                place_tree(
                    place_id,
                    lambda event, pid=place_id: toggle(event, pid),
                    visited,
                )
                for place_id in PLACES[0]["childIds"]
            ]
        ),
    )


@component
def app():
    return travel_plan()
