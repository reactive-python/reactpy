from reactpy import component, html, use_state


# start
@component
def counter(person):
    score, set_score = use_state(0)

    return html.div(
        {"className": "counter"},
        html.h1(f"{person}'s score: {score}"),
        html.button({"onClick": lambda event: set_score(score + 1)}, "Add one"),
    )


@component
def scoreboard():
    is_player_a, set_is_player_a = use_state(True)

    return html.div(
        # Two containers that always exist, so each player's counter has its
        # own position in the tree. Only one holds a counter at a time, and the
        # container that loses it destroys that state.
        #
        # Do not "simplify" this to *([] if cond else [counter(...)]): an empty
        # expansion contributes no children, so both counters end up at
        # position 0 and ReactPy treats them as one component -- no reset.
        html.div(counter("Taylor") if is_player_a else None),
        html.div(counter("Sarah") if not is_player_a else None),
        html.button(
            {"onClick": lambda event: set_is_player_a(not is_player_a)},
            "Next player!",
        ),
    )
