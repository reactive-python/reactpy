from __future__ import annotations

import inspect
from functools import wraps
from typing import Any, Callable, Dict, Optional, Tuple, Union

from .types import ComponentType, VdomDict


def component(
    function: Callable[..., Union[ComponentType, VdomDict | None]]
) -> Callable[..., Component]:
    """A decorator for defining a new component.

    Parameters:
        function: The component's :meth:`idom.core.proto.ComponentType.render` function.
    """
    sig = inspect.signature(function)

    if "key" in sig.parameters and sig.parameters["key"].kind in (
        inspect.Parameter.KEYWORD_ONLY,
        inspect.Parameter.POSITIONAL_OR_KEYWORD,
    ):
        raise TypeError(
            f"Component render function {function} uses reserved parameter 'key'"
        )

    @wraps(function)
    def constructor(*args: Any, key: Optional[Any] = None, **kwargs: Any) -> Component:
        return Component(function, key, args, kwargs, sig)

    return constructor


class Component:
    """An object for rending component models."""

    __slots__ = "__weakref__", "_func", "_args", "_kwargs", "_sig", "key", "type"

    def __init__(
        self,
        function: Callable[..., ComponentType | VdomDict | None],
        key: Optional[Any],
        args: Tuple[Any, ...],
        kwargs: Dict[str, Any],
        sig: inspect.Signature,
    ) -> None:
        self.key = key
        self.type = function
        self._args = args
        self._kwargs = kwargs
        self._sig = sig

    def render(self) -> VdomDict | ComponentType | None:
        return self.type(*self._args, **self._kwargs)

    def should_render(self, new: Component) -> bool:
        return True

    def __repr__(self) -> str:
        try:
            args = self._sig.bind(*self._args, **self._kwargs).arguments
        except TypeError:
            return f"{self.type.__name__}(...)"
        else:
            items = ", ".join(f"{k}={v!r}" for k, v in args.items())
            if items:
                return f"{self.type.__name__}({id(self):02x}, {items})"
            else:
                return f"{self.type.__name__}({id(self):02x})"
