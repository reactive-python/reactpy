from __future__ import annotations

import inspect
from collections.abc import Callable
from functools import wraps
from typing import Any

from reactpy.types import Component, VdomDict


def component(
    function: Callable[..., Component | VdomDict | str | None],
) -> Callable[..., Component]:
    """A decorator for defining a new component.

    Parameters:
        function: The component's :meth:`reactpy.core.proto.ComponentType.render` function.
    """
    sig = inspect.signature(function)

    if "key" in sig.parameters and sig.parameters["key"].kind in (
        inspect.Parameter.KEYWORD_ONLY,
        inspect.Parameter.POSITIONAL_OR_KEYWORD,
    ):
        msg = f"Component render function {function} uses reserved parameter 'key'"
        raise TypeError(msg)

    @wraps(function)
    def constructor(*args: Any, key: Any | None = None, **kwargs: Any) -> Component:
        return Component(function, key, args, kwargs, sig)

    return constructor
