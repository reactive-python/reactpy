from __future__ import annotations

import os
import warnings
from logging import getLogger
from typing import Any, Callable, Generic, TypeVar, cast


_O = TypeVar("_O")
logger = getLogger(__name__)


class Option(Generic[_O]):
    """An option that can be set using an environment variable of the same name"""

    def __init__(
        self,
        name: str,
        default: _O | Option[_O],
        mutable: bool = True,
        validator: Callable[[Any], _O] = lambda x: cast(_O, x),
    ) -> None:
        self._name = name
        self._mutable = mutable
        self._validator = validator
        self._subscribers: list[Callable[[_O], None]] = []

        if name in os.environ:
            self._current = validator(os.environ[name])

        self._default: _O
        if isinstance(default, Option):
            self._default = default.default
            default.subscribe(lambda value: setattr(self, "_default", value))
        else:
            self._default = default

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

    def subscribe(self, handler: Callable[[_O], None]) -> Callable[[_O], None]:
        """Register a callback that will be triggered when this option changes"""
        if not self.mutable:
            raise TypeError("Immutable options cannot be subscribed to.")
        self._subscribers.append(handler)
        handler(self.current)
        return handler

    def is_set(self) -> bool:
        """Whether this option has a value other than its default."""
        return hasattr(self, "_current")

    def set_current(self, new: Any) -> None:
        """Set the value of this option

        Raises a ``TypeError`` if this option is not :attr:`Option.mutable`.
        """
        if not self._mutable:
            raise TypeError(f"{self} cannot be modified after initial load")
        old = self.current
        new = self._current = self._validator(new)
        logger.debug(f"{self._name}={self._current}")
        if new != old:
            for sub_func in self._subscribers:
                sub_func(new)

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
        old = self.current
        delattr(self, "_current")
        if self.current != old:
            for sub_func in self._subscribers:
                sub_func(self.current)

    def __repr__(self) -> str:
        return f"Option({self._name}={self.current!r})"


class DeprecatedOption(Option[_O]):  # pragma: no cover
    def __init__(self, new_opt: Option[_O], name: str) -> None:
        # copy over attrs
        attrs = new_opt.__dict__.copy()
        attrs.pop("_current", None)
        self.__dict__.update(new_opt.__dict__)
        # then set the ones needed here
        self._name = name
        self._new_opt = new_opt

    @property  # type: ignore
    def _current(self) -> _O:
        warnings.warn(
            f"{self.name!r} has been renamed to {self._new_opt.name!r}",
            DeprecationWarning,
        )
        return self._new_opt.current

    @_current.setter
    def _current(self, new: _O) -> None:
        self._new_opt.current = new
