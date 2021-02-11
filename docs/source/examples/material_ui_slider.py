import json

import idom

material_ui = idom.install("@material-ui/core", fallback="loading...")


@idom.component
def ViewSliderEvents():
    event, set_event = idom.hooks.use_state(None)

    return idom.html.div(
        material_ui.Slider(
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
        idom.html.pre(json.dumps(event, indent=2)),
    )


idom.run(ViewSliderEvents)
