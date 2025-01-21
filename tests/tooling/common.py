from typing import Any

from reactpy.core.types import LayoutEventMessage, LayoutUpdateMessage

# see: https://github.com/microsoft/playwright-python/issues/1614
DEFAULT_TYPE_DELAY = 100  # milliseconds


def event_message(target: str, *data: Any) -> LayoutEventMessage:
    return {"type": "layout-event", "target": target, "data": data}


def update_message(path: str, model: Any) -> LayoutUpdateMessage:
    return {"type": "layout-update", "path": path, "model": model}
