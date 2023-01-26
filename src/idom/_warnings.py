from functools import wraps
from inspect import currentframe
from types import FrameType
from typing import Any, Iterator
from warnings import warn as _warn


@wraps(_warn)
def warn(*args: Any, **kwargs: Any) -> Any:
    # warn at call site outside of IDOM
    _warn(*args, stacklevel=_frame_depth_in_module() + 1, **kwargs)  # type: ignore


def _frame_depth_in_module() -> int:
    depth = 0
    for frame in _iter_frames(2):
        module_name = frame.f_globals.get("__name__")
        if not module_name or not module_name.startswith("idom."):
            break
        depth += 1
    return depth


def _iter_frames(index: int = 1) -> Iterator[FrameType]:
    frame = currentframe()
    while frame is not None:
        if index == 0:
            yield frame
        else:
            index -= 1
        frame = frame.f_back
