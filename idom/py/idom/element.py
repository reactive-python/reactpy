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
    """An object for rending element models."""

    __slots__ = (
        "_function",
        "_id",
        "_layout",
        "_state",
        "_updates",
        "_rendered",
    )

    def __init__(self, function: Callable):
        self._function = function
        self._state: State = State(_function_defaults(function))
        self._updates: List[Tuple[Tuple, Dict]] = []
        self._layout: Optional["idom.Layout"] = None
        self._rendered: bool = False
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
        self._updates.append((args, kwargs))
        if self._layout is not None:
            self._layout._update(self)

    def reset(self, *args: Any, **kwargs: Any):
        self._state.update(_function_defaults(self._function))
        self.update(*args, **kwargs)

    def callback(self, function: Callable):
        """Register a callback that will be triggered after rending updates."""
        if self._layout is not None:
            self._layout._callback(function)
        return function

    async def render(self) -> Dict[str, Any]:
        """Render the element's model."""
        parameters = self._load_render_parameters()
        model = self._function(**parameters)
        if inspect.isawaitable(model):
            model = await model
        self._rendered = True
        return model

    def _load_render_parameters(self):
        parameters = {}
        for args, kwargs in self._updates:
            sig = inspect.signature(self._function)
            parameters.update(sig.bind_partial(self, *args, **kwargs).arguments)
        self._state.update(parameters)
        return dict(parameters, **self._state.get())


    def _mount(self, layout: "idom.Layout"):
        self._layout = layout

    def __repr__(self) -> str:
        state = ", ".join("%s=%s" % i for i in self._state.get().items())
        return "%s(%s)" % (self._function.__qualname__, state)


CurrentRef = TypeVar("CurrentRef")


class Ref(Generic[CurrentRef]):

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
        return Ref(self._factory)

    def __repr__(self) -> str:
        return "Ref(%r)" % self.current


class State:

    __slots__ = ("_standard_state", "_referent_state", "_complete_state")

    def __init__(self, initialize: Dict[str, Any]):
        self._standard_state: Dict[str, Any] = {}
        self._referent_state: Dict[str, Ref] = {}
        self._complete_state: Dict[str, Any] = {}
        for k, v in initialize.items():
            if isinstance(v, Ref):
                self._referent_state[k] = v.copy()
            else:
                self._standard_state[k] = v
        self._complete_state = {**self._standard_state, **self._referent_state}

    def update(self, change: Dict[str, Any]):
        for k, v in change.items():
            if isinstance(v, Ref):
                msg = "Cannot pass reference %r to the stateful parameter %r."
                raise TypeError(msg % (v, k))
            elif k in self._referent_state:
                self._referent_state[k].current = v
            elif k in self._standard_state:
                self._standard_state[k] = v
        self._complete_state = {**self._standard_state, **self._referent_state}

    def get(self):
        return self._complete_state


def _function_defaults(function: Callable) -> Dict[str, Any]:
    defaults = {}
    for param in inspect.signature(function).parameters.values():
        if param.default is not inspect.Parameter.empty:
            defaults[param.name] = param.default
    return defaults
