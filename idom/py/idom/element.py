import idom
import uuid
import inspect
from functools import wraps

from typing import (
    List,
    Dict,
    Tuple,
    Callable,
    Iterator,
    Union,
    Any,
    Optional,
    TypeVar,
    Generic,
    Mapping,
)

from .utils import Bunch


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

    __slots__ = (
        "_function",
        "_id",
        "_layout",
        "_state",
        "_updates",
    )

    def __init__(self, function: Callable):
        self._function = function
        self._state: PartialState = PartialState(self._default_state())
        self._updates: List[Tuple[Tuple, Dict]] = []
        self._layout: Optional["idom.Layout"] = None
        self._id = uuid.uuid1().hex

    @property
    def id(self) -> str:
        """The unique ID of the element."""
        return self._id

    @property
    def state(self) -> Bunch:
        return Bunch(self._state.get())

    def update(self, *args: Any, **kwargs: Any):
        """Set the elemenet's state and re-render."""
        if self._layout is not None:
            if len(self._update) == 0:
                # don't tell the layout to render multiple times
                self._layout.element_updated(self)
        self._updates.append((args, kwargs))

    def reset(self, *args: Any, **kwargs: Any):
        self._state.reset(self._default_state())
        self.update(*args, **kwargs)

    def callback(self, function: Callable):
        """Register a callback that will be triggered after rending updates."""
        if self._layout is not None:
            self._layout.element_callback(function)
        return function

    async def render(self) -> Dict[str, Any]:
        """Render the element's model."""
        parameters = self._load_render_parameters()
        model = self._function(**parameters)
        if inspect.isawaitable(model):
            model = await model
        return model

    def _load_render_parameters(self):
        parameters = {}
        for args, kwargs in self._updates:
            sig = inspect.signature(self._function)
            parameters.update(sig.bind_partial(self, *args, **kwargs).arguments)
        self._state.update(parameters, strict=False)
        return dict(parameters, **self._state.get())

    def mount(self, layout: "idom.Layout"):
        self._layout = layout

    def _default_state(self):
        return _function_defaults(self._function)

    def __repr__(self) -> str:
        state = ", ".join("%s=%s" % i for i in self._state.get().items())
        return "%s(%s)" % (self._function.__qualname__, state)


CurrentRef = TypeVar("CurrentRef")


class Ref(Generic[CurrentRef]):
    """Hold a reference to an object for the lifetime of an :class:`Element`.

    This might be useful to determine a user's selection from a list of options:

    .. code-block:: python

        @idom.element
        def option_picker(self, handler, option_names):
            selection = Ref(None)
            options = [option(n, selection) for n in option_names]
            return idom.node("div", options, picker(handler, selection))

        def option(name, selection):
            events = idom.Events()

            @events.on("click")
            def select():
                # set the current selection to the option name
                selection.current = name

            return idom.node("button", eventHandlers=events)

        def picker(handler, selection):
            events = idom.Events()

            @events.on("click")
            def handle():
                # passes the current option name to the handler
                handler(selection.current)

            return idom.node("button", "Use" eventHandlers=events)

    """

    __slots__ = ("current", "_factory")

    def __init__(self, value: CurrentRef = None):
        self._factory: Callable[[], Optional[CurrentRef]]
        if callable(value):
            self._factory = value
        else:
            self._factory = lambda: value
        self.current = self._factory()

    def reset(self):
        self.current = self._factory()

    def copy(self) -> "Ref":
        new = Ref(self._factory)
        new.current = self.current
        return new

    def __repr__(self) -> str:
        return "Ref(%r)" % self.current


class PartialState:
    """Holds state for a subset of fields (which may contain :class:`Ref` objects).

    In short this means that no new keys are added to the state once it has been
    initialized. A "strict" :meth:`PartialState.update` will raise a :class:`KeyError`
    if you attempt to update a field which is not already present. You may set
    ``strict=False`` when updating to silently ignore any unknown fields.

    Parameters:
        partial_state: Sets the initial state and what fields this state contains.

    Notes:

      Fields which contain :class:`Ref` objects are handled differently from those that don't

      1. Upon initializing the state, references are :meth:`copied <Ref.copy>` in
         order to avoid holding the same reference in two different :class:`Element`
         states.

      2. References are never replaced when updating, and no new references are ever
         added to the state. This means that when a field containing a reference is
         updated, only its :attr:`Ref.current` value is changed and when you attempt to
         assign a :class:`Ref` to a field during an update its :attr:`Ref.current` field
         will be used instead.

      3. :meth:`PartialState.reset` calls :meth:`Ref.reset` on all references.
    """

    __slots__ = ("_all_keys", "_ref_keys", "_state")

    def __init__(self, partial_state: Dict[str, Any]):
        self._all_keys: Set[str] = set()
        self._ref_keys: Set[str] = set()
        self._state: Dict[str, Any] = {}
        for k, v in partial_state.items():
            self._all_keys.add(k)
            if isinstance(v, Ref):
                self._ref_keys.add(k)
                # avoid holding the same ref in two different states
                v = v.copy()
            self._state[k] = v

    def update(self, change: Dict[str, Any], strict=True):
        """Update the current state.

        Only fields that are already in the state will be updated. Doing a
        "strict" update will raise if unknown fields are present in the ``change``.

        Parameters:
            change: New state to be adopted.
            strict: Whether an error should be raised if ``change`` contains unknown keys.
        """
        for k, v in change.items():
            if k in self._all_keys:
                # New keys are never added to the state.
                if isinstance(v, Ref):
                    v = v.current
                if k in self._ref_keys:
                    self._state[k].current = v
                else:
                    self._state[k] = v
            elif strict:
                raise KeyError("Unknown key %r." % k)

    def reset(self, reinitialize: Dict[str, Any]):
        """Reset all :class:`Ref` objects and call :meth:`PartialState.update`."""
        for k in self._ref_keys:
            self._state[k].reset()
        self.update(reinitialize)

    def get(self):
        """Get the current state."""
        return self._state


def _function_defaults(function: Callable) -> Dict[str, Any]:
    defaults = {}
    for param in inspect.signature(function).parameters.values():
        if param.default is not inspect.Parameter.empty:
            defaults[param.name] = param.default
    return defaults
