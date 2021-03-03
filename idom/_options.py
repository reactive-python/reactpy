import os
from typing import Any, Callable, Dict, Type

IDOM_DEBUG_MODE = False


def _load_os_environ() -> None:
    from_string: Dict[Type[Any], Callable[[Any], Any]] = {
        bool: lambda v: bool(int(v)),
    }

    module = globals()
    for name, default in globals().items():
        if not name.startswith("_") and name.upper() == name:
            value_type = type(default)
            value = os.environ.get(name, default)
            if value_type in from_string:
                value = from_string[value_type](value)
            module[name] = value

    return None


_load_os_environ()
