import json

import idom

material_ui = idom.install("@material-ui/core", fallback="loading...")


@idom.component
def ViewButtonEvents():
    event, set_event = idom.hooks.use_state(None)

    return idom.html.div(
        material_ui.Button(
            {
                "color": "primary",
                "variant": "contained",
                "onClick": lambda event: set_event(event),
            },
            "Click Me!",
        ),
        idom.html.pre(json.dumps(event, indent=2)),
    )


idom.run(ViewButtonEvents)
