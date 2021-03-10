from __future__ import annotations

import os
from typing import Any, Callable, Generic, TypeVar, cast


_O = TypeVar("_O")


class Option(Generic[_O]):
    """An option that can be set using an environment variable of the same name"""

    def __init__(
        self,
        name: str,
        default: _O,
        immutable: bool = False,
        validator: Callable[[Any], _O] = lambda x: cast(_O, x),
    ) -> None:
        self.name = name
        self._default = default
        self._immutable = immutable
        self._validator = validator
        self._value = validator(os.environ.get(name, default))

    def get(self) -> _O:
        return self._value

    def set(self, new: _O) -> _O:
        if self._immutable:
            raise TypeError(f"{self} cannot be modified after initial load")
        old = self._value
        self._value = self._validator(new)
        return old

    def reset(self) -> _O:
        return self.set(self._default)

    def __repr__(self) -> str:
        return f"Option(name={self.name!r}, value={self._value!r})"
