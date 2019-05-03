import abc
import inspect
from functools import wraps

from typing_extensions import Protocol
from typing import Dict, Callable, Any, List, Optional, overload, Awaitable

import idom

from .utils import bound_id


ElementConstructor = Callable[..., "Element"]  # Element constructor


class _EF(Protocol):
    """Element function."""

    def __call__(
        self, element: "Element", *args: Any, **kwargs: Any
    ) -> Awaitable[Dict[str, Any]]:
        ...


@overload
def element(function: Callable[..., Any]) -> ElementConstructor:
    ...


@overload
def element(*, state: Optional[str] = None) -> Callable[[_EF], ElementConstructor]:
    ...


def element(
    function: Optional[_EF] = None, state: Optional[str] = None
) -> Callable[..., Any]:
    """A decorator for defining an :class:`Element`.

    Parameters:
        function: The function that will render a :term:`VDOM` model.
    """

    def setup(func: _EF) -> ElementConstructor:
        @wraps(func)
        def constructor(*args: Any, **kwargs: Any) -> Element:
            element = Element(func, state)
            element.update(*args, **kwargs)
            return element

        return constructor

    if function is not None:
        return setup(function)
    else:
        return setup


class AbstractElement(abc.ABC):

    __slots__ = ["_element_id", "_layout"]

    if not hasattr(abc.ABC, "__weakref__"):
        __slots__.append("__weakref__")

    def __init__(self) -> None:
        self._layout: Optional["idom.Layout"] = None
        self._element_id = bound_id(self)

    @property
    def id(self) -> str:
        """The unique ID of the element."""
        return self._element_id

    @abc.abstractmethod
    async def render(self) -> Dict[str, Any]:
        ...

    def mount(self, layout: "idom.Layout") -> None:
        """Mount a layout to the element instance.

        Occurs just before rendering the element for the **first** time.
        """
        self._layout = layout

    def mounted(self) -> bool:
        """Whether or not this element is associated with a layout."""
        return self._layout is not None


class Element(AbstractElement):
    """An object for rending element models.

    Rendering element objects is typically done by a :class:`idom.layout.Layout` which
    will :meth:`Element.mount` itself to the element instance the first time it is rendered.
    From there an element instance will communicate its needs to the layout. For example
    when an element wants to re-render it will call :meth:`idom.layout.Layout.element_updated`.

    The lifecycle of an element typically goes in this order:

    1. The element instance is instantiated.

    2. The element's layout will mount itself.

    3. The layout will call :meth:`Element.render`.

    4. The element is dormant until an :meth:`Element.update` occurs.

    5. Go back to step **3**.
    """

    __slots__ = (
        "_function",
        "_function_signature",
        "_state",
        "_state_parameters",
        "_update",
    )

    def __init__(self, function: _EF, state_parameters: Optional[str]):
        super().__init__()
        self._function = function
        self._function_signature = inspect.signature(function)
        self._layout: Optional["idom.Layout"] = None
        self._state: Dict[str, Any] = {}
        self._state_parameters: List[str] = list(
            map(str.strip, (state_parameters or "").split(","))
        )
        self._update: Optional[Dict[str, Any]] = None

    def update(self, *args: Any, **kwargs: Any) -> None:
        """Schedule this element to render with new parameters."""
        if self._update is None:
            # only tell layout to render on first update call
            self._update = {}
            if self._layout is not None:
                self._layout.update(self)
        bound = self._function_signature.bind_partial(None, *args, **kwargs)
        self._update.update(list(bound.arguments.items())[1:])

    def animate(
        self, function: Callable[[], Awaitable[None]]
    ) -> Callable[[], Awaitable[None]]:
        """Schedule this function to run soon, and then render any updates it caused."""
        if self._layout is not None:
            # animating and updating an element is redundant.
            self._layout.animate(function)
        return function

    async def render(self) -> Dict[str, Any]:
        """Render the element's :term:`VDOM` model."""
        # load update and reset for next render
        update = self._update

        if update is None:
            raise RuntimeError(f"{self} cannot render again - no update occured.")

        for name in self._state_parameters:
            if name not in update:
                if name in self._state:
                    update[name] = self._state[name]
            else:
                self._state[name] = update[name]

        self._update = None

        return await self._function(self, **update)

    def __repr__(self) -> str:
        qualname = getattr(self._function, "__qualname__", None)
        if qualname is not None:
            return "%s(%s)" % (qualname, self.id)
        else:
            return "%s(%r, %r)" % (type(self).__name__, self._function, self.id)
