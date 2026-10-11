import json

import reactpy


@reactpy.component
def PlayDinosaurSound():
    event, set_event = reactpy.hooks.use_state(None)

    async def handle_time_update(event):
        set_event(event)

    return reactpy.html.div(
        reactpy.html.audio(
            {
                "controls": True,
                "on_time_update": handle_time_update,
                "src": "https://interactive-examples.mdn.mozilla.net/media/cc0-audio/t-rex-roar.mp3",
            }
        ),
        reactpy.html.pre(json.dumps(event, indent=2)),
    )


reactpy.run(PlayDinosaurSound)
