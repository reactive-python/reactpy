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
        # Both branches render counter() at the same position, so without a key
        # ReactPy would treat them as the same component and carry the score
        # from one player to the next. The key gives each player their own
        # identity, so switching players resets the score.
        counter("Taylor", key="Taylor")
        if is_player_a
        else counter("Sarah", key="Sarah"),
        html.button(
            {"onClick": lambda event: set_is_player_a(not is_player_a)},
            "Next player!",
        ),
    )
