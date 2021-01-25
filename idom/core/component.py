import abc
import inspect
from functools import wraps
from typing import TYPE_CHECKING, Dict, Callable, Any, Tuple, Union


if TYPE_CHECKING:  # pragma: no cover
    from .vdom import VdomDict  # noqa


ComponentConstructor = Callable[..., "Component"]
ComponentRenderFunction = Callable[..., Union["AbstractComponent", "VdomDict"]]


def component(function: ComponentRenderFunction) -> Callable[..., "Component"]:
    """A decorator for defining an :class:`Component`.

    Parameters:
        function:
            The function that will render a :ref:`VDOM <VDOM Mimetype>` model.
    """

    @wraps(function)
    def constructor(*args: Any, **kwargs: Any) -> Component:
        return Component(function, args, kwargs)

    return constructor


class AbstractComponent(abc.ABC):

    __slots__ = [] if hasattr(abc.ABC, "__weakref__") else ["__weakref__"]

    @abc.abstractmethod
    def render(self) -> "VdomDict":
        """Render the component's :ref:`VDOM <VDOM Mimetype>` model."""


class Component(AbstractComponent):
    """An object for rending component models."""

    __slots__ = (
        "_function",
        "_args",
        "_kwargs",
    )

    def __init__(
        self,
        function: ComponentRenderFunction,
        args: Tuple[Any, ...],
        kwargs: Dict[str, Any],
    ) -> None:
        self._function = function
        self._args = args
        self._kwargs = kwargs

    def render(self) -> Any:
        return self._function(*self._args, **self._kwargs)

    def __repr__(self) -> str:
        sig = inspect.signature(self._function)
        args = sig.bind(*self._args, **self._kwargs).arguments
        items = ", ".join(f"{k}={v!r}" for k, v in args.items())
        if items:
            return f"{self._function.__name__}({hex(id(self))}, {items})"
        else:
            return f"{self._function.__name__}({hex(id(self))})"
