import json

import reactpy


@reactpy.component
def PlayDinosaurSound():
    event, set_event = reactpy.hooks.use_state(None)
    return reactpy.html.div(
        reactpy.html.audio(
            {
                "controls": True,
                "on_time_update": lambda e: set_event(e),
                "src": "https://interactive-examples.mdn.mozilla.net/media/cc0-audio/t-rex-roar.mp3",
            }
        ),
        reactpy.html.pre(json.dumps(event, indent=2)),
    )


reactpy.run(PlayDinosaurSound)
