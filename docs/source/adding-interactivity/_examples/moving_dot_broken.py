from idom import component, html, run, use_state


@component
def MovingDot():
    position, set_position = use_state({"x": 0, "y": 0})

    def handle_click(event):
        position["x"] = event["clientX"]
        position["y"] = event["clientY"]
        set_position(position)

    return html.div(
        {
            "onClick": handle_click,
            "style": {
                "position": "relative",
                "height": "200px",
                "width": "100%",
                "backgroundColor": "white",
            },
        },
        html.div(
            {
                "style": {
                    "position": "absolute",
                    "backgroundColor": "red",
                    "borderRadius": "50%",
                    "width": "20px",
                    "height": "20px",
                    "left": "-10px",
                    "top": "-10px",
                    "transform": f"translate({position['x']}px, {position['y']}px)",
                },
            }
        ),
    )


run(MovingDot)
