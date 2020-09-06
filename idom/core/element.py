import abc
import inspect
from functools import wraps
from typing import TYPE_CHECKING, Dict, Callable, Any, Tuple, Union


if TYPE_CHECKING:  # pragma: no cover
    from .vdom import VdomDict  # noqa


ElementConstructor = Callable[..., "Element"]
ElementRenderFunction = Callable[..., Union["AbstractElement", "VdomDict"]]


def element(function: ElementRenderFunction) -> Callable[..., "Element"]:
    """A decorator for defining an :class:`Element`.

    Parameters:
        function:
            The function that will render a :ref:`VDOM <VDOM Mimetype>` model.
    """

    @wraps(function)
    def constructor(*args: Any, **kwargs: Any) -> Element:
        return Element(function, args, kwargs)

    return constructor


class AbstractElement(abc.ABC):

    __slots__ = [] if hasattr(abc.ABC, "__weakref__") else ["__weakref__"]

    @abc.abstractmethod
    def render(self) -> "VdomDict":
        """Render the element's :ref:`VDOM <VDOM Mimetype>` model."""


class Element(AbstractElement):
    """An object for rending element models.

    Rendering element objects is typically done by a :class:`idom.core.layout.Layout` which
    will :meth:`Element.mount` itself to the element instance the first time it is rendered.
    From there an element instance will communicate its needs to the layout. For example
    when an element wants to re-render it will call :meth:`idom.core.layout.Layout.element_updated`.

    The life cycle of an element typically goes in this order:

    1. The element instance is instantiated.

    2. The layout will call :meth:`Element.render`.

    3. The element is dormant until an :meth:`Element.update` occurs.

    4. Go back to step **2**.
    """

    __slots__ = (
        "_function",
        "_args",
        "_kwargs",
    )

    def __init__(
        self,
        function: ElementRenderFunction,
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
            return f"{self._function.__name__}:{id(self)}({items})"
        else:
            return f"{self._function.__name__}:{id(self)}()"
