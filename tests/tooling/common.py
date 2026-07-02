from typing import Any

from reactpy.types import LayoutEventMessage, LayoutUpdateMessage


def event_message(target: str, *data: Any) -> LayoutEventMessage:
    return {"type": "layout-event", "target": target, "data": data}


def update_message(path: str, model: Any) -> LayoutUpdateMessage:
    return {"type": "layout-update", "path": path, "model": model}
