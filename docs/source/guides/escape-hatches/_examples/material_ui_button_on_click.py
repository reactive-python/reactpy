import json

import reactpy


mui = reactpy.web.module_from_template(
    "react@^17.0.0",
    "@material-ui/core@4.12.4",
    fallback="⌛",
)
Button = reactpy.web.export(mui, "Button")


@reactpy.component
def ViewButtonEvents():
    event, set_event = reactpy.hooks.use_state(None)

    return reactpy.html.div(
        Button(
            {
                "color": "primary",
                "variant": "contained",
                "onClick": lambda event: set_event(event),
            },
            "Click Me!",
        ),
        reactpy.html.pre(json.dumps(event, indent=2)),
    )


reactpy.run(ViewButtonEvents)
