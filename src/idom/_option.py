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
        mutable: bool = True,
        validator: Callable[[Any], _O] = lambda x: cast(_O, x),
    ) -> None:
        self.name = name
        self._default = default
        self._mutable = mutable
        self._validator = validator
        self._value = validator(os.environ.get(name, default))

    @property
    def mutable(self) -> bool:
        """Whether this option can be modified after being loaded"""
        return self._mutable

    def get(self) -> _O:
        """Get the current value of this option."""
        return self._value

    def set(self, new: _O) -> _O:
        """Set the value of this configuration option

        Raises a ``TypeError`` if this option is immutable.
        """
        if not self._mutable:
            raise TypeError(f"{self} cannot be modified after initial load")
        old = self._value
        self._value = self._validator(new)
        return old

    def reset(self) -> _O:
        """Reset the value of this option to its default setting"""
        return self.set(self._default)

    def __repr__(self) -> str:
        return f"Option({self.name}={self._value!r})"
