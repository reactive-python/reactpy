from typing import Any


def hex_id(obj: Any) -> str:
    return format(id(obj), "x")
