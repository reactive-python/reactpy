from __future__ import annotations

import inspect
from types import FrameType


def f_module_name(index: int = 0) -> str:
    frame = f_back(index + 1)
    if frame is None:
        return ""  # nocov
    name = frame.f_globals.get("__name__", "")
    if not isinstance(name, str):
        raise TypeError("Expected module name to be a string")  # nocov
    return name


def f_back(index: int = 0) -> FrameType | None:
    frame = inspect.currentframe()
    while frame is not None:
        if index < 0:
            return frame
        frame = frame.f_back
        index -= 1
    return None  # nocov
