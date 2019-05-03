import inspect
from base64 import b64encode
from io import BytesIO

from typing import (
    Any,
    Callable,
    Dict,
    TypeVar,
    Generic,
    List,
    Tuple,
    Iterator,
    Optional,
    Mapping,
    Union,
)

from .bunch import DynamicBunch
from .utils import bound_id
from .element import AbstractElement, ElementConstructor, Element, element


def node(tag: str, *children: Any, **attributes: Any) -> DynamicBunch:
    """A helper function for generating :term:`VDOM` dictionaries."""
    merged_children: List[Any] = []

    for c in children:
        if isinstance(c, (list, tuple)):
            merged_children.extend(c)
        else:
            merged_children.append(c)

    model = DynamicBunch(tagName=tag)

    if merged_children:
        model.children = merged_children
    if "eventHandlers" in attributes:
        model.eventHandlers = attributes.pop("eventHandlers")
    if attributes:
        model.attributes = attributes

    return model


def node_constructor(
    tag: str, allow_children: bool = True
) -> Callable[..., DynamicBunch]:
    """Create a constructor for nodes with the given tag name."""

    def constructor(*children: Any, **attributes: Any) -> DynamicBunch:
        if not allow_children and children:
            raise TypeError(f"{tag!r} nodes cannot have children.")
        return node(tag, *children, **attributes)

    constructor.__name__ = tag
    qualname_prefix = constructor.__qualname__.rsplit(".", 1)[0]
    constructor.__qualname__ = qualname_prefix + f".{tag}"
    constructor.__doc__ = f"""Create a new ``<{tag}/>`` - returns :term:`VDOM`."""
    return constructor


def hotswap() -> Tuple[Callable[[ElementConstructor], None], ElementConstructor]:
    var: Var[Optional[Element]] = Var(None)

    @element
    async def HotSwap(self: Element, element: Optional[Element] = None) -> Any:
        var.set(self)
        return element or {"tagName": "div"}

    def swap(element: ElementConstructor, *args: Any, **kwargs: Any) -> None:
        hot = var.get()
        if hot is None:
            raise RuntimeError("Element has not been displayed.")
        else:
            hot.update(element=element(*args, **kwargs))

    return swap, HotSwap


_EHF = TypeVar("_EHF", bound=Callable[..., Any])  # event handler function


class Events(Mapping[str, "EventHandler"]):
    """A container for event handlers.

    Assign this object to the ``"eventHandlers"`` field of an element model.
    """

    __slots__ = ("_handlers",)

    def __init__(self) -> None:
        self._handlers: Dict[str, EventHandler] = {}

    def on(self, event: str, where: Optional[str] = None) -> Callable[[_EHF], _EHF]:
        """A decorator for adding an event handler.

        Parameters:
            event:
                The camel-case name of the event, the word "on" is automatically
                prepended. So passing "keyDown" would refer to the event "onKeyDown".
            where:
                A string defining what event attribute a parameter refers to if the
                parameter name does not already refer to it directly. See the
                :class:`EventHandler` class for more info.

        Returns:
            A decorator which accepts an event handler function as its first argument.
            The parameters of the event handler function may indicate event attributes
            which should be sent back from the frontend. See :class:`EventHandler` for
            more info.

        Examples:
            Simple "onClick" event handler:

            .. code-block:: python

                def clickable_element():
                    my_button = Events()

                    @events.on("click")
                    def handler():
                        # do something on a click event
                        ...

                    return idom.node("button", "hello!", eventHandlers=events)

            Getting an ``<input/>`` element's current value when it changes:

            .. code-block:: python

                def input_element():
                    events = Events()

                    @events.on("keyDown", where="value=target.value")
                    def handle_input_element_change(value)
                        # do something with the input's new value
                        ...

                    return idon.node("input", "type here...", eventHandlers=events)
        """
        event_name = "on" + event[:1].upper() + event[1:]

        def setup(function: _EHF) -> _EHF:
            self._handlers[event_name] = EventHandler(function, event_name, where)
            return function

        return setup

    def __len__(self) -> int:
        return len(self._handlers)

    def __iter__(self) -> Iterator[str]:
        return iter(self._handlers)

    def __getitem__(self, key: str) -> "EventHandler":
        return self._handlers[key]

    def __repr__(self) -> str:
        return repr(self._handlers)


class EventHandler:
    """An object which defines an event handler.

    Get a serialized reference to the handler via :meth:`EventHandler.serialize`.

    The event handler object acts like a coroutine even if the given function was not.

    Parameters:
        function:
            The event handler function. Its parameters may indicate event attributes
            which should be sent back from the fronend unless otherwise specified by
            the ``where`` parameter.
        event_name:
            The camel case name of the event.
        where:
            A string defining what event attribute a parameter refers to if the
            parameter name does not already refer to it directly. For example,
            accessing the current value of an ``<input/>`` element might be done
            by specifying ``where="param=target.value"``.
        target_id:
            A unique identifier for the event handler. This is generally used if
            an element has more than on event handler for the same event type. If
            no ID is provided one will be generated automatically.
    """

    __slots__ = (
        "_function",
        "_handler",
        "_event_name",
        "_target_id",
        "_props_to_params",
        "__weakref__",
    )

    def __init__(
        self,
        function: _EHF,
        event_name: str,
        where: Optional[str] = None,
        target_id: Optional[str] = None,
    ) -> None:
        self._function = function
        self._handler = function
        self._target_id = target_id or bound_id(self)
        self._event_name = event_name
        self._props_to_params: Dict[str, str] = {}
        for target_key, param in inspect.signature(function).parameters.items():
            if param.kind in (
                inspect.Parameter.VAR_POSITIONAL,
                inspect.Parameter.VAR_KEYWORD,
            ):
                raise TypeError(
                    f"Event handler {function} has variable keyword or positional arguments."
                )
            self._props_to_params.setdefault(target_key, target_key)
        if where is not None:
            for part in map(str.strip, where.split(",")):
                target_key, source_prop = tuple(map(str.strip, part.split("=")))
                self._props_to_params[source_prop] = target_key
                try:
                    self._props_to_params.pop(target_key)
                except KeyError:
                    raise TypeError(
                        f"Event handler {function} has no parameter {target_key!r}."
                    )

    async def __call__(self, data: Dict[str, Any]) -> Any:
        data = {self._props_to_params[k]: v for k, v in data.items()}
        return await self._handler(**data)

    def serialize(self) -> str:
        string = f"{self._target_id}_{self._event_name}"
        if self._props_to_params:
            string += f"_{';'.join(self._props_to_params.keys())}"
        return string

    def __repr__(self) -> str:
        return repr(self.serialize())

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, EventHandler):
            return (
                self._function == other._function
                and self._target_id == other._target_id
                and self._event_name == other._event_name
                and self._props_to_params == other._props_to_params
            )
        else:
            return bool(other == self._function)


_R = TypeVar("_R", bound=Any)  # Var reference


class Var(Generic[_R]):
    """A variable for holding a reference to an object.

    Variables are useful when multiple elements need to share data. This is usually
    discouraged, but can be useful in certain situations. For example, you might use
    a reference to keep track of a user's selection from a list of options:

    .. code-block:: python

        def option_picker(handler, option_names):
            selection = Var()
            options = [option(n, selection) for n in option_names]
            return idom.node("div", options, picker(handler, selection))

        def option(name, selection):
            events = idom.Events()

            @events.on("click")
            def select():
                # set the current selection to the option name
                selection.set(name)

            return idom.node("button", eventHandlers=events)

        def picker(handler, selection):
            events = idom.Events()

            @events.on("click")
            def handle():
                # passes the current option name to the handler
                handler(selection.get())

            return idom.node("button", "Use" eventHandlers=events)
    """

    __slots__ = ("__current",)

    def __init__(self, value: _R) -> None:
        self.__current = value

    def set(self, new: _R) -> _R:
        old = self.__current
        self.__current = new
        return old

    def get(self) -> _R:
        return self.__current

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Var):
            return bool(self.get() == other.get())
        else:
            return False

    def __repr__(self) -> str:
        return "Var(%r)" % self.get()


class Image(AbstractElement):

    __slots__ = ("_source", "_format", "_buffer")

    def __init__(self, format: str, value: str = ""):
        super().__init__()
        if format == "svg":
            format = "svg+xml"
        self._buffer = BytesBuffer(value.encode(), self._set_source)
        self._source = b""
        self._format = format

    @property
    def io(self) -> "BytesBuffer":
        return self._buffer

    async def render(self) -> Dict[str, Any]:
        self._buffer.close()
        source = b64encode(self._source).decode()
        return {
            "tagName": "img",
            "attributes": {"src": f"data:image/{self._format};base64,{source}"},
        }

    def _set_source(self, value: bytes) -> None:
        self._source = value


class BytesBuffer(BytesIO):
    def __init__(
        self, value: Union[bytes, str], close_callback: Callable[[bytes], None]
    ) -> None:
        self._on_close_callback = close_callback
        if isinstance(value, str):
            super().__init__(value.encode())
        else:
            super().__init__(value)

    def write(self, value: Union[bytes, str]) -> int:
        if isinstance(value, str):
            return super().write(value.encode())
        else:
            return super().write(value)

    def close(self) -> None:
        if not self.closed:
            self._on_close_callback(self.getvalue())
        super().close()
