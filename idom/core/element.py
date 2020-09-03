import abc
import inspect
from uuid import uuid4
from functools import wraps
from typing import TYPE_CHECKING, Dict, Callable, Any, Awaitable, Tuple


if TYPE_CHECKING:  # pragma: no cover
    from .vdom import VdomDict  # noqa


ElementConstructor = Callable[..., "Element"]
ElementRenderFunction = Callable[..., Awaitable["VdomDict"]]


def element(function: ElementRenderFunction) -> Callable[..., "Element"]:
    """A decorator for defining an :class:`Element`.

    Parameters:
        function:
            The function that will render a :term:`VDOM` model.
    """
    if not inspect.iscoroutinefunction(function):
        raise TypeError(f"Expected a coroutine function, not {function}")

    @wraps(function)
    def constructor(*args: Any, **kwargs: Any) -> Element:
        return Element(function, args, kwargs)

    return constructor


class AbstractElement(abc.ABC):

    __slots__ = ["_id"]

    if not hasattr(abc.ABC, "__weakref__"):  # pragma: no cover
        __slots__.append("__weakref__")

    def __init__(self) -> None:
        # we can't use `id(self)` because IDs are regularly re-used and the layout
        # relies on unique IDs to determine which elements have been deleted
        self._id = uuid4().hex

    @property
    def id(self) -> str:
        """The unique ID of the element."""
        return self._id

    @abc.abstractmethod
    async def render(self) -> "VdomDict":
        """Render the element's :term:`VDOM` model."""


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
        super().__init__()
        self._function = function
        self._args = args
        self._kwargs = kwargs

    async def render(self) -> Any:
        return await self._function(*self._args, **self._kwargs)

    def __repr__(self) -> str:
        sig = inspect.signature(self._function)
        args = sig.bind(*self._args, **self._kwargs).arguments
        items = ", ".join(f"{k}={v!r}" for k, v in args.items())
        if items:
            return f"{self._function.__name__}({self.id}, {items})"
        else:
            return f"{self._function.__name__}({self.id})"
