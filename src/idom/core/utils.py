import os
import uuid
from weakref import finalize

from typing import Set, Any


STATIC_DIRECTORY = os.path.join(os.path.dirname(__file__), "..", "static")


def bound_id(obj: Any, size: int = 10) -> str:
    obj_id = uuid.uuid4().hex[:size]
    while obj_id in _LOCAL_IDS:
        obj_id = uuid.uuid4().hex[:size]
    _LOCAL_IDS.add(obj_id)

    def remove_obj_id() -> None:
        _LOCAL_IDS.remove(obj_id)

    finalize(obj, remove_obj_id)
    return obj_id


_LOCAL_IDS: Set[str] = set()
