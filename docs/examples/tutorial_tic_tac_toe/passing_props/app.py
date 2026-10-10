from reactpy import component, html


# start
@component
def square(value):
    return html.button({"className": "square"}, value)


@component
def board():
    return html.fragment(
        html.div(
            {"className": "board-row"},
            square("A"),
            square("B"),
            square("C"),
        ),
        html.div(
            {"className": "board-row"},
            square("D"),
            square("E"),
            square("F"),
        ),
        html.div(
            {"className": "board-row"},
            square("G"),
            square("H"),
            square("I"),
        ),
    )
