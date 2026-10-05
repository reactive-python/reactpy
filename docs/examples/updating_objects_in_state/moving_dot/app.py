from reactpy import component, html, use_state


# start
@component
def moving_dot():
    position, set_position = use_state({"x": 0, "y": 0})

    def handle_move(event):
        # Replace the whole object: ReactPy never merges a partial update.
        set_position({"x": event["clientX"], "y": event["clientY"]})

    return html.div(
        {
            "onPointerMove": handle_move,
            "style": {
                "position": "relative",
                "width": "100%",
                "height": "180px",
                "background": "#f0f0f0",
            },
        },
        html.div(
            {
                "style": {
                    "position": "absolute",
                    "background": "black",
                    "borderRadius": "50%",
                    "width": "20px",
                    "height": "20px",
                    "left": "-10px",
                    "top": "-10px",
                    "transform": f"translate({position['x']}px, {position['y']}px)",
                }
            }
        ),
    )
