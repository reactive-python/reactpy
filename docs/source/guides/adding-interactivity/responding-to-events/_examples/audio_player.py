import json

import idom


@idom.component
def PlayDinosaurSound():
    event, set_event = idom.hooks.use_state(None)
    return idom.html.div(
        idom.html.audio(
            {
                "controls": True,
                "on_time_update": lambda e: set_event(e),
                "src": "https://interactive-examples.mdn.mozilla.net/media/cc0-audio/t-rex-roar.mp3",
            }
        ),
        idom.html.pre(json.dumps(event, indent=2)),
    )


idom.run(PlayDinosaurSound)
