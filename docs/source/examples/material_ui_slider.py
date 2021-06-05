import json

import idom


material_ui = idom.install("@material-ui/core", fallback="loading...")


@idom.component
def ViewSliderEvents():
    (event, value), set_data = idom.hooks.use_state((None, 50))

    return idom.html.div(
        material_ui.Slider(
            {
                "color": "primary" if value < 50 else "secondary",
                "step": 10,
                "min": 0,
                "max": 100,
                "defaultValue": 50,
                "valueLabelDisplay": "auto",
                "onChange": lambda event, value: set_data([event, value]),
            }
        ),
        idom.html.pre(json.dumps([event, value], indent=2)),
    )


idom.run(ViewSliderEvents)
