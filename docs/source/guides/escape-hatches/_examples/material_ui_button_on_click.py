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

    async def handle_click(event):
        set_event(event)

    return reactpy.html.div(
        Button(
            {
                "color": "primary",
                "variant": "contained",
                "onClick": handle_click,
            },
            "Click Me!",
        ),
        reactpy.html.pre(json.dumps(event, indent=2)),
    )


reactpy.run(ViewButtonEvents)
