import abc
import idom
import uuid
import inspect
from functools import wraps
from weakref import WeakValueDictionary

from typing import (
    List,
    Dict,
    Tuple,
    Callable,
    Iterator,
    Union,
    Any,
    Optional,
    Mapping,
)

from .utils import Bunch, to_coroutine


def element(function: Callable) -> Callable:
    @wraps(function)
    def constructor(*args: Any, **kwargs: Any) -> Element:
        element = Element(function)
        element.update(*args, **kwargs)
        return element
    return constructor


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
        "_function",
        "_function_signature",
        "_id",
        "_layout",
        "_update",
        "__weakref__",
    )

    @classmethod
    def by_id(self, element_id: str) -> "Element":
        return self._by_id[element_id]

    def __init__(self, function: Callable):
        self._function = to_coroutine(function)
        self._function_signature = inspect.signature(function)
        self._update: Optional[Dict] = None
        self._layout: Optional["idom.Layout"] = None
        self._id = uuid.uuid1().hex
        self._by_id[self._id] = self
        self._dead: bool = False

    @property
    def id(self) -> str:
        """The unique ID of the element."""
        return self._id

    def update(self, *args: Any, **kwargs: Any):
        """Schedule this element to render with new parameters."""
        if self._layout is not None:
            if self._update is None:
                self._layout.update(self)
        bound = self._function_signature.bind(None, *args, **kwargs)
        self._update = dict(list(bound.arguments.items())[1:])

    def animate(self, function: Callable, loop=False):
        """Schedule this function to run soon, and then render any updates."""
        if self._layout is not None:
            if self._update is None:
                # animating and updating an element is redundant.
                self._layout.animate(function)
        return function

    async def render(self) -> Dict[str, Any]:
        """Render the element's model."""
        if self._update is None:
            raise RuntimeError(f"Rendered {self} twice.")
        update = self._update
        self._update = None
        return (await self._function(self, **update))

    def mount(self, layout: "idom.Layout"):
        if not self._dead:
            self._layout = layout

    def unmount(self):
        self._layout = None
        self._dead = True

    def __repr__(self) -> str:
        return "%s(%s)" % (self._function.__qualname__, self.id)
