"""
Config Option
=============
"""

from __future__ import annotations

import os
from logging import getLogger
from typing import Any, Callable, Generic, TypeVar, cast


_O = TypeVar("_O")
logger = getLogger(__name__)


class Option(Generic[_O]):
    """An option that can be set using an environment variable of the same name"""

    def __init__(
        self,
        name: str,
        default: _O,
        mutable: bool = True,
        validator: Callable[[Any], _O] = lambda x: cast(_O, x),
    ) -> None:
        self._name = name
        self._default = default
        self._mutable = mutable
        self._validator = validator
        if name in os.environ:
            self._current = validator(os.environ[name])
        logger.debug(f"{self._name}={self.current}")

    @property
    def name(self) -> str:
        """The name of this option (used to load environment variables)"""
        return self._name

    @property
    def mutable(self) -> bool:
        """Whether this option can be modified after being loaded"""
        return self._mutable

    @property
    def default(self) -> _O:
        """This option's default value"""
        return self._default

    @property
    def current(self) -> _O:
        try:
            return self._current
        except AttributeError:
            return self._default

    @current.setter
    def current(self, new: _O) -> None:
        self.set_current(new)
        return None

    def is_set(self) -> bool:
        """Whether this option has a value other than its default."""
        return hasattr(self, "_current")

    def set_current(self, new: Any) -> None:
        """Set the value of this option

        Raises a ``TypeError`` if this option is not :attr:`Option.mutable`.
        """
        if not self._mutable:
            raise TypeError(f"{self} cannot be modified after initial load")
        self._current = self._validator(new)
        logger.debug(f"{self._name}={self._current}")

    def set_default(self, new: _O) -> _O:
        """Set the value of this option if not :meth:`Option.is_set`

        Returns the current value (a la :meth:`dict.set_default`)
        """
        if not self.is_set():
            self.set_current(new)
        return self._current

    def reload(self) -> None:
        """Reload this option from its environment variable"""
        self.set_current(os.environ.get(self._name, self._default))

    def unset(self) -> None:
        """Remove the current value, the default will be used until it is set again."""
        if not self._mutable:
            raise TypeError(f"{self} cannot be modified after initial load")
        delattr(self, "_current")

    def __repr__(self) -> str:
        return f"Option({self._name}={self.current!r})"
