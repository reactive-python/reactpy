import json

import idom


material_ui = idom.Module("@material-ui/core")
Slider = material_ui.Import("Slider", fallback="loading...")

material_ui_style = idom.html.link(
    {
        "rel": "stylesheet",
        "href": "https://fonts.googleapis.com/css?family=Roboto:300,400,500,700&display=swap",
    }
)


@idom.element
def SliderOnPaper():
    event, set_event = idom.hooks.use_state(None)

    return idom.html.div(
        material_ui_style,
        Slider(
            {
                "color": "primary",
                "step": 10,
                "min": 0,
                "max": 100,
                "defaultValue": 50,
                "valueLabelDisplay": "auto",
                "onChange": lambda *event: set_event(event),
            }
        ),
        json.dumps(event, indent=2),
    )


display(SliderOnPaper)
