from typing import Any

from reactpy.testing.common import GITHUB_ACTIONS
from reactpy.types import LayoutEventMessage, LayoutUpdateMessage

DEFAULT_TYPE_DELAY = 250 if GITHUB_ACTIONS else 50


def event_message(target: str, *data: Any) -> LayoutEventMessage:
    return {"type": "layout-event", "target": target, "data": data}


def update_message(path: str, model: Any) -> LayoutUpdateMessage:
    return {"type": "layout-update", "path": path, "model": model}
