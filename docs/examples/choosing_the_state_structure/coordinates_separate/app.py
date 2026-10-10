"""Two state variables that must move together — and one handler that forgets."""

from reactpy import component, html, use_state

STEP = 24
BOARD = 240

STYLE = {
    "position": "relative",
    "width": f"{BOARD}px",
    "height": f"{BOARD}px",
    "background": "#f0f0f0",
    "marginTop": "8px",
}


# start
@component
def marker():
    x, set_x = use_state(20)
    y, set_y = use_state(20)

    def move_diagonally(event):
        # The classic mistake: this handler remembers x and forgets y.
        set_x(x + STEP)

    def move_correctly(event):
        set_x(x + STEP)
        set_y(y + STEP)

    def reset(event):
        set_x(20)
        set_y(20)

    return html.div(
        html.button({"onClick": move_diagonally}, "Move (forgot y)"),
        html.button({"onClick": move_correctly}, "Move (both)"),
        html.button({"onClick": reset}, "Reset"),
        html.div(
            STYLE,
            html.div(
                {
                    "style": {
                        "position": "absolute",
                        "left": f"{x}px",
                        "top": f"{y}px",
                        "width": "18px",
                        "height": "18px",
                        "borderRadius": "50%",
                        "background": "#d40000",
                    }
                }
            ),
        ),
        html.p({"id": "coords"}, f"x={x}  y={y}"),
    )


@component
def app():
    return html.div(html.h3("Two state variables"), marker())
