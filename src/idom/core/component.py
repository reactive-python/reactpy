from __future__ import annotations

import abc
import inspect
from functools import wraps
from typing import Any, Callable, Dict, Optional, Tuple, Union

from .utils import hex_id
from .vdom import VdomDict


ComponentConstructor = Callable[..., "AbstractComponent"]
ComponentRenderFunction = Callable[..., Union["AbstractComponent", VdomDict]]


def component(function: ComponentRenderFunction) -> Callable[..., "Component"]:
    """A decorator for defining an :class:`Component`.

    Parameters:
        function:
            The function that will render a :ref:`VDOM <VDOM Mimetype>` model.
    """

    @wraps(function)
    def constructor(*args: Any, key: Optional[Any] = None, **kwargs: Any) -> Component:
        return Component(function, key, args, kwargs)

    return constructor


class AbstractComponent(abc.ABC):

    __slots__ = ["key"]
    if not hasattr(abc.ABC, "__weakref__"):
        __slots__.append("__weakref__")  # pragma: no cover

    key: Optional[Any]

    @abc.abstractmethod
    def render(self) -> VdomDict:
        """Render the component's :ref:`VDOM <VDOM Mimetype>` model."""


class Component(AbstractComponent):
    """An object for rending component models."""

    __slots__ = "_func", "_args", "_kwargs"

    def __init__(
        self,
        function: ComponentRenderFunction,
        key: Optional[Any],
        args: Tuple[Any, ...],
        kwargs: Dict[str, Any],
    ) -> None:
        self.key = key
        self._func = function
        self._args = args
        self._kwargs = kwargs
        if key is not None:
            kwargs["key"] = key

    def render(self) -> VdomDict:
        model = self._func(*self._args, **self._kwargs)
        if isinstance(model, AbstractComponent):
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
                return f"{self._func.__name__}({hex_id(self)}, {items})"
            else:
                return f"{self._func.__name__}({hex_id(self)})"
