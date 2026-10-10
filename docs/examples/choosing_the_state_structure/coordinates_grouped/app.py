"""One state variable, so there is no second setter to forget."""

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
    position, set_position = use_state({"x": 20, "y": 20})

    def move_diagonally(event):
        # One setter, one object: there is no second call left to forget.
        set_position({"x": position["x"] + STEP, "y": position["y"] + STEP})

    def reset(event):
        set_position({"x": 20, "y": 20})

    return html.div(
        html.button({"onClick": move_diagonally}, "Move diagonally"),
        html.button({"onClick": reset}, "Reset"),
        html.div(
            STYLE,
            html.div(
                {
                    "style": {
                        "position": "absolute",
                        "left": f"{position['x']}px",
                        "top": f"{position['y']}px",
                        "width": "18px",
                        "height": "18px",
                        "borderRadius": "50%",
                        "background": "#d40000",
                    }
                }
            ),
        ),
        html.p({"id": "coords"}, f"x={position['x']}  y={position['y']}"),
    )


@component
def app():
    return html.div(html.h3("One state variable"), marker())
