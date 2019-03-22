import idom
import inspect
from functools import wraps
from weakref import WeakValueDictionary

from typing import Dict, Callable, Any, List, Optional, overload

from .utils import to_coroutine, bound_id


_ElementConstructor = Callable[..., "Element"]


@overload
def element(function: Callable) -> _ElementConstructor:
    ...


@overload
def element(
    *, state: Optional[str] = None
) -> Callable[[Callable], _ElementConstructor]:
    ...


def element(
    function: Optional[Callable] = None, state: Optional[str] = None
) -> Callable:
    """A decorator for defining an :class:`Element`.

    Parameters:
        function: The function that will render a :term:`VDOM` model.
    """

    def setup(func):
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


class Element:
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

    _by_id = WeakValueDictionary()  # type: WeakValueDictionary[str, "Element"]

    __slots__ = (
        "_dead",
        "_element_id",
        "_function",
        "_function_signature",
        "_layout",
        "_state",
        "_state_parameters",
        "_update",
        "__weakref__",
    )

    @classmethod
    def by_id(self, element_id: str) -> "Element":
        """Get an element instance given its :attr:`Element.id`."""
        return self._by_id[element_id]

    def __init__(self, function: Callable, state_parameters: Optional[str]):
        self._dead: bool = False
        self._element_id = bound_id(self)
        self._function = to_coroutine(function)
        self._function_signature = inspect.signature(function)
        self._layout: Optional["idom.Layout"] = None
        self._state: Dict[str, Any] = {}
        self._state_parameters: List[str] = list(
            map(str.strip, (state_parameters or "").split(","))
        )
        self._update: Optional[Dict[str, Any]] = None
        # save self to "by-ID" mapping
        Element._by_id[self._element_id] = self

    @property
    def id(self) -> str:
        """The unique ID of the element."""
        return self._element_id

    def update(self, *args: Any, **kwargs: Any):
        """Schedule this element to render with new parameters."""
        if self._update is None:
            # only tell layout to render on first update call
            self._update = {}
            if self._layout is not None:
                self._layout.update(self)
        bound = self._function_signature.bind_partial(None, *args, **kwargs)
        self._update.update(list(bound.arguments.items())[1:])

    def animate(self, function: Callable):
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

    def mount(self, layout: "idom.Layout"):
        """Mount a layout to the element instance.

        Occurs just before rendering the element.
        """
        if not self._dead:
            self._layout = layout

    def unmount(self):
        """Unmount a layout from the element instance.

        Occurs when a parent element has re-rendered and its old children are deleted.
        """
        self._layout = None
        self._dead = True

    def __repr__(self) -> str:
        return "%s(%s)" % (self._function.__qualname__, self.id)
