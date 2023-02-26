from __future__ import annotations

import inspect
from types import FrameType


def f_module_name(index: int = 0) -> str:
    frame = f_back(index + 1)
    if frame is None:
        return ""  # pragma: no cover
    name = frame.f_globals.get("__name__", "")
    assert isinstance(name, str), "Expected module name to be a string"
    return name


def f_back(index: int = 0) -> FrameType | None:
    frame = inspect.currentframe()
    while frame is not None:
        if index < 0:
            return frame
        frame = frame.f_back
        index -= 1
    return None  # pragma: no cover
