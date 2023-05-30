from pathlib import Path
from typing import NamedTuple

from reactpy import component, html, run, use_state
from reactpy.widgets import image

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
    position, set_position = use_state(Position(100, 100, 0))

    return html.div(
        {"style": {"width": "225px"}},
        html.div(
            {
                "style": {
                    "width": "200px",
                    "height": "200px",
                    "background_color": "slategray",
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
        html.button(
            {"on_click": lambda e: set_position(translate(x=-10))}, "Move Left"
        ),
        html.button(
            {"on_click": lambda e: set_position(translate(x=10))}, "Move Right"
        ),
        html.button({"on_click": lambda e: set_position(translate(y=-10))}, "Move Up"),
        html.button({"on_click": lambda e: set_position(translate(y=10))}, "Move Down"),
        html.button({"on_click": lambda e: set_position(rotate(-30))}, "Rotate Left"),
        html.button({"on_click": lambda e: set_position(rotate(30))}, "Rotate Right"),
    )


run(Scene)
