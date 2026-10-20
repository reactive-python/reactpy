from reactpy import component, html, use_state


# start
@component
def square(value, on_click):
    return html.button({"className": "square", "onClick": on_click}, value)


@component
def board():
    initial_board: list[str | None] = [None] * 9
    squares, set_squares = use_state(initial_board)

    def handle_click(i):
        async def inner(event):
            if squares[i]:
                return
            next_squares = squares.copy()
            next_squares[i] = "X"
            set_squares(next_squares)

        return inner

    return html.fragment(
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
