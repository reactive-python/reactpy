from typing import Any, Callable, Dict, Type

IDOM_DEBUG = False


def _init() -> None:
    """Collect options from :attr:`os.environ`"""
    import os

    from_string: Dict[Type[Any], Callable[[Any], Any]] = {
        bool: lambda v: bool(int(v)),
    }

    module = globals()
    for name, default in globals().items():
        value_type = type(default)
        value = os.environ.get(name, default)
        if value_type in from_string:
            value = from_string[value_type](value)
        module[name] = value

    return None


_init()
