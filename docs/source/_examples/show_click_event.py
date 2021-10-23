import json

import idom


@idom.component
def BasicButton():
    event, set_event = idom.hooks.use_state(None)
    return idom.html.div(
        idom.html.button({"onClick": lambda e: set_event(e)}, "click to see event"),
        idom.html.pre(json.dumps(event, indent=2)),
    )


idom.run(BasicButton)
