from pathlib import Path
from typing import NamedTuple

from idom import component, html, run, use_state
from idom.widgets import image


HERE = Path(__file__)
CHARACTER_IMAGE = (HERE.parent / "static" / "bunny.png").read_bytes()


class Position(NamedTuple):
    x: int
    y: int
    angle: int


def rotate(degrees):
    return lambda old_position: Position(
        old_position.x,
        old_position.y,
        old_position.angle + degrees,
    )


def translate(x=0, y=0):
    return lambda old_position: Position(
        old_position.x + x,
        old_position.y + y,
        old_position.angle,
    )


@component
def Scene():
    actions, set_actions = use_state(())
    position, set_position = use_state(Position(100, 100, 0))

    def handle_apply_actions(event):
        for act_function in actions:
            set_position(act_function)
        set_actions(())

    def make_action_handler(act_function):
        return lambda event: set_actions(actions + (act_function,))

    return html.div(
        {"style": {"width": "225px"}},
        html.div(
            {
                "style": {
                    "width": "200px",
                    "height": "200px",
                    "backgroundColor": "slategray",
                }
            },
            image(
                "png",
                CHARACTER_IMAGE,
                {
                    "style": {
                        "position": "relative",
                        "left": f"{position.x}px",
                        "top": f"{position.y}.px",
                        "transform": f"rotate({position.angle}deg) scale(2, 2)",
                    }
                },
            ),
        ),
        html.button({"onClick": make_action_handler(translate(x=-10))}, "Move Left"),
        html.button({"onClick": make_action_handler(translate(x=10))}, "Move Right"),
        html.button({"onClick": make_action_handler(translate(y=-10))}, "Move Up"),
        html.button({"onClick": make_action_handler(translate(y=10))}, "Move Down"),
        html.button({"onClick": make_action_handler(rotate(-30))}, "Rotate Left"),
        html.button({"onClick": make_action_handler(rotate(30))}, "Rotate Right"),
        html.button({"onClick": handle_apply_actions}, html.b("Apply Actions")),
    )


run(Scene)
