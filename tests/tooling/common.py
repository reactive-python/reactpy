from typing import Any

from reactpy.testing import DEFAULT_TYPE_DELAY
from reactpy.types import LayoutEventMessage, LayoutUpdateMessage

# Per-character delays to type at when a test needs keystrokes to arrive faster than
# the server can answer them. ``0`` leaves the client running well ahead of the
# server. A few milliseconds is the awkward zone where the server lands exactly one
# keystroke behind, which is precisely where a snapshot of the previous keystroke
# can be mistaken for a current one and written back over what the user typed.
# ``DEFAULT_TYPE_DELAY`` is slower than the server and is what the rest of the suite
# uses. Typing has to work at every one of them - a test which only passes at the
# slowest value is timing its way past a real bug.
TYPE_DELAYS = list(dict.fromkeys([0, 5, 10, DEFAULT_TYPE_DELAY]))


def event_message(target: str, *data: Any) -> LayoutEventMessage:
    return {"type": "layout-event", "target": target, "data": data}


def update_message(path: str, model: Any) -> LayoutUpdateMessage:
    return {"type": "layout-update", "path": path, "model": model}
