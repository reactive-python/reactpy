from reactpy import component, html, use_memo, use_state

# start

ROSTER = [
    ("ada", 91),
    ("grace", 120),
    ("alan", 77),
    ("edsger", 64),
    ("katherine", 143),
    ("dorothy", 88),
    ("margaret", 155),
]

sorts = []  # demo-only: lets you *see* how often `rank` actually runs


@component
def leaderboard():
    players, set_players = use_state(
        [{"name": name, "score": score} for name, score in ROSTER]
    )
    highlight, set_highlight = use_state("ada")

    def rank():
        # The work you want to skip: sorting the whole table. Listing
        # `dependencies=[players]` runs this only when the roster changes, so
        # changing the highlight leaves the sorted list alone.
        sorts.append(1)
        return sorted(players, key=lambda player: -player["score"])

    ranked = use_memo(rank, dependencies=[players])

    return html.div(
        html.h1("Leaderboard"),
        html.ol([html.li(f"{player['name']}: {player['score']}") for player in ranked]),
        html.p(f"sorted {len(sorts)} time(s)"),
        html.p(f"highlighted: {highlight}"),
        html.button(
            {
                "onClick": lambda event: set_highlight(
                    "grace" if highlight == "ada" else "ada"
                )
            },
            "Change highlight",
        ),
        html.button(
            {
                "onClick": lambda event: set_players(
                    [{**player, "score": player["score"] + 1} for player in players]
                )
            },
            "Everyone scores +1",
        ),
    )
