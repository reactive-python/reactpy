import sys
import abc
import idom
import uuid
import inspect
from functools import wraps
from weakref import WeakValueDictionary

from typing import (
    Dict,
    Callable,
    Any,
    Tuple,
    Optional,
)

from .utils import to_coroutine


def element(function: Callable) -> Callable:
    """A decorator for defining an :class:`Element`.

    Parameters:
        function: The function that will render a :term:`VDOM` model.
    """

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
        "_cycles",
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
        """Get an element instance given its :attr:`Element.id`."""
        return self._by_id[element_id]

    def __init__(self, function: Callable):
        self._dead: bool = False
        self._function = to_coroutine(function)
        self._function_signature = inspect.signature(function)
        self._id = uuid.uuid1().hex
        self._layout: Optional["idom.Layout"] = None
        self._update: Dict[str, Any] = {}
        # initialize the element's cycles
        self._cycles: Dict[str, Cycle] = {}
        for name, param in self._function_signature.parameters.items():
            if isinstance(param.default, Cycle._constructor):
                self._cycles[name] = param.default(self, name)
        # save self to "by-ID" mapping
        Element._by_id[self._id] = self

    @property
    def id(self) -> str:
        """The unique ID of the element."""
        return self._id

    def update(self, *args: Any, **kwargs: Any):
        """Schedule this element to render with new parameters."""
        if self._layout is not None:
            if not self._update:
                self._layout.update(self)
        bound = self._function_signature.bind(None, *args, **kwargs)
        self._update = dict(list(bound.arguments.items())[1:])

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
        self._update = {}
        # enter cycles
        for k, c in self._cycles.items():
            c.enter(update)
        try:
            # render the model
            model = await self._function(self, **update)
        finally:
            # exit cycles
            for c in self._cycles.values():
                c.exit(*sys.exc_info())
        # finally return it
        return model

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


class Cycle(abc.ABC):
    """An abstract base class for hooking into the :class:`Element` lifecycle.

    Cycles are added to elements by passing them as default arguments of an element's
    rendering function:

    .. code-block:: python

        @idom.element
        def my_element(self, my_cycle=MyCycle()): ...

    Cycles will be triggered just before and just after an element is rendered. You
    are able to hook into these events by defining either of the optional
    :meth:`Element.enter` and :meth:`Element.exit` methods.

    Examples:
        See :class:`idom.helpers.State` to see how cycles can be used.

    Notes:
        Subclasses of :class:`Cycle` should not overwrite ``__new__`` because
        this has a special implementation. If you absolutely must overwrite it,
        ``__new__`` is required to return a :class:`Cycle._constructor`.
    """

    def __new__(cls, *args: Any, **kwargs: Any) -> Callable[[Element, str], "Cycle"]:
        return cls._constructor(super().__new__(cls), args, kwargs)

    def __init__(self, element: Element, name: str):
        self._element = element
        self._name = name

    def enter(self, update: Dict[str, Any]):
        """Called just before an element is rendered.

        Parameters:
            update:
                The parameters which will be passed to the element. You are free to
                modify these as you wish.
        """

    def exit(self, exception_type, exception_value, traceback):
        """Called just after an element is rendered.

        This takes the same parameters as :meth:`object.__exit__`.
        """

    class _constructor:

        def __init__(self, cycle: "Cycle", args: Tuple[Any, ...], kwargs: Dict[str, Any]):
            self._cycle = cycle
            self._args = args
            self._kwargs = kwargs

        def __call__(self, element: Element, name: str):
            self._cycle.__init__(element, name, *self._args, **self._kwargs)
            return self._cycle
