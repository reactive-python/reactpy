import idom
import uuid
import inspect

from typing import List, Dict, Tuple, Callable, Iterator, Union, Any, Optional, TypeVar, Generic, Mapping

from .utils import Bunch


def element(function: Callable) -> Callable:
    def constructor(*args: Any, **kwargs: Any) -> Element:
        return Element(function).update(*args, **kwargs)

    return constructor


class Element:
    """An object for rending element models."""

    __slots__ = ("_function", "_id", "_layout", "_state", "_rendered")

    def __init__(self, function: Callable):
        self._function = function
        initial_state = {}
        for param in inspect.signature(function).parameters.values():
            if param.default is not inspect.Parameter.empty:
                initial_state[param.name] = param.default
        self._state: State = State(initial_state)
        self._layout: Optional["idom.Layout"] = None
        self._rendered: bool = False
        self._id = uuid.uuid4().hex

    @property
    def id(self) -> str:
        """The unique ID of the element."""
        return self._id

    @property
    def state(self) -> Bunch:
        return Bunch(self._state.get())

    def reset(self, *args: Any, **kwargs: Any):
        """Clear the element's state and render."""
        self._state.reset()
        self.update(*args, **kwargs)

    def update(self, *args: Any, **kwargs: Any) -> "Element":
        """Set the elemenet's state and re-render."""
        sig = inspect.signature(self._function)
        bound = sig.bind_partial(None, *args, **kwargs).arguments
        self._state.update(list(bound.items())[1:])
        if self._rendered and self._layout is not None:
            self._layout._update(self)
            self._rendered = False
        return self

    def callback(self, function: Callable):
        """Register a callback that will be triggered after rending updates."""
        if self._layout is not None:
            self._layout._callback(function)

    async def render(self) -> Dict[str, Any]:
        """Render the element's model."""
        model = self._function(self, **self._state.get())
        if inspect.isawaitable(model):
            model = await model
        self._rendered = True
        return model

    def _mount(self, layout: "idom.Layout"):
        self._layout = layout

    def __repr__(self) -> str:
        state = ", ".join("%s=%s" % i for i in self._state.get().items())
        return "%s(%s)" % (self._function.__qualname__, state)


class State:

    __slots__ = ("_data")

    def __init__(self, data: Mapping = None):
        self._data: Dict[str, Any] = {}
        self.update(data or {})

    def get(self) -> Dict:
        return self._data

    def update(self, *args: Any, **kwargs: Any):
        for k, v in dict(*args, **kwargs).items():
            if isinstance(v, Context):
                # we don't want this to be shared between sessions
                v = v.copy()
            if isinstance(self._data.get(k), Context):
                self._data[k].current = v
            else:
                self._data[k] = v

    def reset(self):
        for k, v in tuple(self._data.items()):
            if isinstance(v, Context):
                v.reset()
            else:
                del self._data[k]


CurrentContext = TypeVar("CurrentContext")


class Context(Generic[CurrentContext]):

    __slots__ = ("current", "_factory")

    def __init__(self, value: CurrentContext = None):
        self._factory: Callable[[], Optional[CurrentContext]]
        if callable(value):
            self._factory = value
        else:
            self._factory = lambda: value
        self.current = self._factory()

    def reset(self):
        self.current = self._factory()

    def copy(self) -> "Context":
        return Context(self._factory)
