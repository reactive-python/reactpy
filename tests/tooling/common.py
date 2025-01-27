import os
from typing import Any

from reactpy.types import LayoutEventMessage, LayoutUpdateMessage

GITHUB_ACTIONS = os.getenv("GITHUB_ACTIONS", "False")
DEFAULT_TYPE_DELAY = (
    250 if GITHUB_ACTIONS.lower() in {"y", "yes", "t", "true", "on", "1"} else 25
)


def event_message(target: str, *data: Any) -> LayoutEventMessage:
    return {"type": "layout-event", "target": target, "data": data}


def update_message(path: str, model: Any) -> LayoutUpdateMessage:
    return {"type": "layout-update", "path": path, "model": model}
