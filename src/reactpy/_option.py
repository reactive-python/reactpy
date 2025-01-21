from __future__ import annotations

import os
from logging import getLogger
from typing import Any, Callable, Generic, TypeVar, cast

from reactpy._warnings import warn

_O = TypeVar("_O")
logger = getLogger(__name__)
UNDEFINED = cast(Any, object())


class Option(Generic[_O]):
    """An option that can be set using an environment variable of the same name"""

    def __init__(
        self,
        name: str,
        default: _O = UNDEFINED,
        mutable: bool = True,
        parent: Option[_O] | None = None,
        validator: Callable[[Any], _O] = lambda x: cast(_O, x),
    ) -> None:
        self._name = name
        self._mutable = mutable
        self._validator = validator
        self._subscribers: list[Callable[[_O], None]] = []

        if name in os.environ:
            self._current = validator(os.environ[name])

        if parent is not None:
            if not (parent.mutable and self.mutable):
                raise TypeError("Parent and child options must be mutable")
            self._default = parent.default
            parent.subscribe(self.set_current)
        elif default is not UNDEFINED:
            self._default = default
        else:
            raise TypeError("Must specify either a default or a parent option")

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

    @current.deleter
    def current(self) -> None:
        self.unset()

    def subscribe(self, handler: Callable[[_O], None]) -> Callable[[_O], None]:
        """Register a callback that will be triggered when this option changes"""
        if not self.mutable:
            msg = "Immutable options cannot be subscribed to."
            raise TypeError(msg)
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
        old = self.current
        if new is old:
            return None

        if not self._mutable:
            msg = f"{self} cannot be modified after initial load"
            raise TypeError(msg)

        try:
            new = self._current = self._validator(new)
        except ValueError as error:
            raise ValueError(f"Invalid value for {self._name}: {new!r}") from error

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
            msg = f"{self} cannot be modified after initial load"
            raise TypeError(msg)
        old = self.current
        if hasattr(self, "_current"):
            delattr(self, "_current")
        if self.current != old:
            for sub_func in self._subscribers:
                sub_func(self.current)

    def __repr__(self) -> str:
        return f"Option({self._name}={self.current!r})"


class DeprecatedOption(Option[_O]):
    """An option that will warn when it is accessed"""

    def __init__(self, *args: Any, message: str, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._deprecation_message = message

    @Option.current.getter  # type: ignore
    def current(self) -> _O:
        try:
            # we access the current value during init to debug log it
            # no need to warn unless it's actually used. since this attr
            # is only set after super().__init__ is called, we can check
            # for it to determine if it's being accessed by a user.
            msg = self._deprecation_message
        except AttributeError:
            pass
        else:
            warn(msg, DeprecationWarning)
        return super().current
