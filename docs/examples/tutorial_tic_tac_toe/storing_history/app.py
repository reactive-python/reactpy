from reactpy import component, html, use_state


@component
def square(value, on_click):
    return html.button({"className": "square", "onClick": on_click}, value)


@component
def board(x_is_next, squares, on_play):
    def handle_click(i):
        def inner(event):
            if calculate_winner(squares) or squares[i]:
                return
            next_squares = squares.copy()
            next_squares[i] = "X" if x_is_next else "O"
            on_play(next_squares)

        return inner

    winner = calculate_winner(squares)
    status = (
        f"Winner: {winner}" if winner else "Next player: " + ("X" if x_is_next else "O")
    )

    return html.fragment(
        html.div({"className": "status"}, status),
        html.div(
            {"className": "board-row"},
            square(squares[0], handle_click(0)),
            square(squares[1], handle_click(1)),
            square(squares[2], handle_click(2)),
        ),
        html.div(
            {"className": "board-row"},
            square(squares[3], handle_click(3)),
            square(squares[4], handle_click(4)),
            square(squares[5], handle_click(5)),
        ),
        html.div(
            {"className": "board-row"},
            square(squares[6], handle_click(6)),
            square(squares[7], handle_click(7)),
            square(squares[8], handle_click(8)),
        ),
    )


# start
@component
def game():
    history, set_history = use_state([[None] * 9])

    def handle_play(next_squares):
        set_history([*history, next_squares])

    current_move = len(history) - 1
    x_is_next = current_move % 2 == 0
    current_squares = history[current_move]

    return html.div(
        {"className": "game"},
        html.div(
            {"className": "game-board"},
            board(x_is_next, current_squares, handle_play),
        ),
        html.div({"className": "game-info"}, html.ol()),
    )


def calculate_winner(squares):
    lines = [
        [0, 1, 2],
        [3, 4, 5],
        [6, 7, 8],
        [0, 3, 6],
        [1, 4, 7],
        [2, 5, 8],
        [0, 4, 8],
        [2, 4, 6],
    ]
    for a, b, c in lines:
        if squares[a] and squares[a] == squares[b] and squares[a] == squares[c]:
            return squares[a]
    return None
