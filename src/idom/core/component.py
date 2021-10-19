"""
Component
=========
"""

from __future__ import annotations

import inspect
import warnings
from functools import wraps
from typing import Any, Callable, Dict, Optional, Tuple, Type, TypeVar, Union, overload

from .hooks import use_effect, use_state
from .proto import ComponentType, VdomDict


_Class = TypeVar("_Class", bound=Type[ComponentType])


@overload
def component(function_or_class: _Class) -> _Class:
    ...


@overload
def component(function_or_class: Callable[..., Any]) -> Callable[..., ComponentType]:
    ...


def component(function_or_class: Any) -> Callable[..., ComponentType]:
    """A decorator for defining an :class:`Component`.

    Parameters:
        function: The function that will render a :class:`VdomDict`.
    """
    if not inspect.isclass(function_or_class):
        return _wrap_function(function_or_class)
    else:
        return _wrap_class(function_or_class)


def set_state(cmpt: Any, state: Any) -> None:
    """A function for re-rendering a class-based component with updated state"""
    try:
        set_state = cmpt._set_state
    except AttributeError:
        if isinstance(cmpt, ComponentType):
            raise RuntimeError("Cannot update a component that has not rendered yet")
        else:
            raise TypeError(f"{cmpt} is not a component class")
    else:
        set_state(state)


def _wrap_function(
    function: Callable[..., ComponentType | VdomDict]
) -> Callable[..., Component]:
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


class Component:
    """An object for rending component models."""

    __slots__ = "__weakref__", "_func", "_args", "_kwargs", "key"

    def __init__(
        self,
        function: Callable[..., Union[ComponentType, VdomDict]],
        key: Optional[Any],
        args: Tuple[Any, ...],
        kwargs: Dict[str, Any],
    ) -> None:
        self._args = args
        self._func = function
        self._kwargs = kwargs
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
                return f"{self._func.__name__}({id(self)}, {items})"
            else:
                return f"{self._func.__name__}({id(self)})"


_Wrapped = TypeVar("_Wrapped", bound=Any)


def _wrap_class(cls: type[_Wrapped]) -> type[_Wrapped]:
    """Modifies the given class such that it can operate as a stateful component

    Adds the following attributes to the class:

    - ``key``
    - ``state``
    - ``_set_state``

    And wraps the following methods with extra logic that is opaque to the user:

    - ``__init__``
    - ``render``
    """

    if hasattr(cls, "__slots__") and "__dict__" not in cls.__slots__:
        missing_slots = list({"key", "state", "_set_state"}.difference(cls.__slots__))
        if missing_slots:
            raise ValueError("Component classes requires __slots__ for {missing_slots}")

    old_init = getattr(cls, "__init__", object.__init__)
    old_render = cls.render

    @wraps(old_init)
    def new_init(self: Any, *args: Any, key: Any | None = None, **kwargs: Any) -> None:
        self.key = key
        self.state = None
        old_init(self, *args, **kwargs)

    @wraps(old_render)
    def new_render(self: Any) -> Any:
        self.state, self._set_state = use_state(self.state)  # noqa: ROH101
        use_effect(getattr(self, "effect", None), args=[])  # noqa: ROH101
        return old_render(self)

    # wrap the original methods
    cls.__init__ = _OwnerInheritorDescriptor(new_init, old_init)
    cls.render = _OwnerInheritorDescriptor(new_render, old_render)
    # manually set up descriptor
    cls.__init__.__set_name__(cls, "__init__")
    cls.render.__set_name__(cls, "render")

    return cls


class _OwnerInheritorDescriptor:
    """Show one value for the owner of this descriptor and another for the owner's subclass

    Example:
        .. code-block::

            class Owner:
                method = _OwnerInheritorDescriptor(
                    own_method=lambda self: 1,
                    inherited_method=lambda self: 2,
                )

            class Inheritor(Owner):
                def method(self):
                    return super().method()

            assert Owner().method() == 1
            assert Inheritor().method() == 2
    """

    owner: type[Any]

    def __init__(
        self,
        own_method: Any,
        inherited_method: Any,
    ) -> None:
        self.own_method = own_method
        self.inherited_method = inherited_method

    def __set_name__(self, cls: type[Any], name: str) -> None:
        self.owner = cls

    def __get__(self, obj: Any | None, cls: type[Any]) -> Any:
        if obj is None:
            return self
        elif cls is self.owner:
            return self.own_method.__get__(obj, cls)
        else:
            return self.inherited_method.__get__(obj, cls)
