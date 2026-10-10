from reactpy import component, html


# start
@component
def board():
    return html.fragment(
        html.div(
            {"className": "board-row"},
            html.button({"className": "square"}, "1"),
            html.button({"className": "square"}, "2"),
            html.button({"className": "square"}, "3"),
        ),
        html.div(
            {"className": "board-row"},
            html.button({"className": "square"}, "4"),
            html.button({"className": "square"}, "5"),
            html.button({"className": "square"}, "6"),
        ),
        html.div(
            {"className": "board-row"},
            html.button({"className": "square"}, "7"),
            html.button({"className": "square"}, "8"),
            html.button({"className": "square"}, "9"),
        ),
    )
