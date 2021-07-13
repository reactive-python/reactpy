"""
Component
=========
"""

from __future__ import annotations

import abc
import inspect
import warnings
from functools import wraps
from typing import Any, Callable, Dict, Optional, Tuple, Union
from uuid import uuid4

from typing_extensions import Protocol, runtime_checkable

from .vdom import VdomDict


ComponentConstructor = Callable[..., "ComponentType"]
ComponentRenderFunction = Callable[..., Union["ComponentType", VdomDict]]


def component(function: ComponentRenderFunction) -> Callable[..., "Component"]:
    """A decorator for defining an :class:`Component`.

    Parameters:
        function: The function that will render a :class:`VdomDict`.
    """
    sig = inspect.signature(function)
    key_is_kwarg = "key" in sig.parameters and sig.parameters["key"].kind in (
        inspect.Parameter.KEYWORD_ONLY,
        inspect.Parameter.POSITIONAL_OR_KEYWORD,
    )
    if key_is_kwarg:  # pragma: no cover
        warnings.warn(
            f"Component render function {function} uses reserved parameter 'key' - this "
            "will produce an error in a future release",
            DeprecationWarning,
        )

    @wraps(function)
    def constructor(*args: Any, key: Optional[Any] = None, **kwargs: Any) -> Component:
        if key_is_kwarg:
            kwargs["key"] = key
        return Component(function, key, args, kwargs)

    return constructor


@runtime_checkable
class ComponentType(Protocol):
    """The expected interface for all component-like objects"""

    id: str
    key: Optional[Any]

    @abc.abstractmethod
    def render(self) -> VdomDict:
        """Render the component's :class:`VdomDict`."""


class Component:
    """An object for rending component models."""

    __slots__ = "__weakref__", "_func", "_args", "_kwargs", "id", "key"

    def __init__(
        self,
        function: ComponentRenderFunction,
        key: Optional[Any],
        args: Tuple[Any, ...],
        kwargs: Dict[str, Any],
    ) -> None:
        self._args = args
        self._func = function
        self._kwargs = kwargs
        self.id = uuid4().hex
        self.key = key

    def render(self) -> VdomDict:
        model = self._func(*self._args, **self._kwargs)
        if isinstance(model, ComponentType):
            model = {"tagName": "div", "children": [model]}
        return model

    def __repr__(self) -> str:
        sig = inspect.signature(self._func)
        try:
            args = sig.bind(*self._args, **self._kwargs).arguments
        except TypeError:
            return f"{self._func.__name__}(...)"
        else:
            items = ", ".join(f"{k}={v!r}" for k, v in args.items())
            if items:
                return f"{self._func.__name__}({self.id}, {items})"
            else:
                return f"{self._func.__name__}({self.id})"
