from reactpy import component, html, run, use_state


@component
def MovingDot():
    position, set_position = use_state({"x": 0, "y": 0})

    async def handle_pointer_move(event):
        outer_div_info = event["currentTarget"]
        outer_div_bounds = outer_div_info["boundingClientRect"]
        set_position(
            {
                "x": event["clientX"] - outer_div_bounds["x"],
                "y": event["clientY"] - outer_div_bounds["y"],
            }
        )

    return html.div(
        {
            "on_pointer_move": handle_pointer_move,
            "style": {
                "position": "relative",
                "height": "200px",
                "width": "100%",
                "background_color": "white",
            },
        },
        html.div(
            {
                "style": {
                    "position": "absolute",
                    "background_color": "red",
                    "border_radius": "50%",
                    "width": "20px",
                    "height": "20px",
                    "left": "-10px",
                    "top": "-10px",
                    "transform": f"translate({position['x']}px, {position['y']}px)",
                }
            }
        ),
    )


run(MovingDot)
