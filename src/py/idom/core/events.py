import inspect
from weakref import proxy, CallableProxyType
from functools import partial
from typing import (
    Mapping,
    Dict,
    Callable,
    Any,
    Optional,
    Iterator,
    Set,
    List,
    Tuple,
    Awaitable,
)

from .utils import bound_id
from .element import AbstractElement


_EHF = Callable[..., Awaitable[Any]]  # event handler function


class Events(Mapping[str, "EventHandler"]):
    """A container for event handlers.

    Assign this object to the ``"eventHandlers"`` field of an element model.
    """

    __slots__ = ("_handlers", "_bound")

    def __init__(self, bound: Optional[AbstractElement] = None) -> None:
        self._handlers: Dict[str, EventHandler] = {}
        self._bound: Optional[CallableProxyType] = None
        if bound is not None:
            self._bound = proxy(bound)

    def on(
        self,
        event: str,
        using: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Callable[[_EHF], _EHF]:
        """A decorator for adding an event handler.

        Parameters:
            event:
                The camel-case name of the event, the word "on" is automatically
                prepended. So passing "keyDown" would refer to the event "onKeyDown".
            using:
                A string defining what event attribute a parameter refers to if the
                parameter name does not already refer to it directly. See the
                :class:`EventHandler` class for more info.
            options:
                See :meth:`EventHandler.configure` for more details.

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

                    @events.on("keyDown", using="value=target.value")
                    def handle_input_element_change(value)
                        # do something with the input's new value
                        ...

                    return idon.node("input", "type here...", eventHandlers=events)
        """
        event_name = "on" + event[:1].upper() + event[1:]

        if event_name not in self._handlers:
            handler = self._handlers[event_name] = EventHandler(event_name)
        else:
            handler = self._handlers[event_name]
        if options is not None:
            handler.configure(**options)

        def setup(function: _EHF) -> _EHF:
            if self._bound is not None:
                function = partial(function, self._bound)
            handler.add(function, using)
            return function

        return setup

    def __contains__(self, key: Any) -> bool:
        return key in self._handlers

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

    The event handler object acts like a coroutine when called.

    Parameters:
        event_name:
            The camel case name of the event.
        target_id:
            A unique identifier for the event handler. This is generally used if
            an element has more than on event handler for the same event type. If
            no ID is provided one will be generated automatically.
    """

    __slots__ = (
        "_handler_info",
        "_target_id",
        "_event_name",
        "__weakref__",
        "_prevent_default",
        "_stop_propogation",
    )

    def __init__(self, event_name: str, target_id: Optional[str] = None) -> None:
        self._handler_info: List[Tuple[_EHF, Dict[str, str]]] = []
        self._target_id = target_id or bound_id(self)
        self._event_name = event_name
        self._prevent_default = False
        self._stop_propogation = False

    @property
    def id(self) -> str:
        return self._target_id

    def configure(
        self, preventDefault: bool = False, stopPropagation: bool = False
    ) -> "EventHandler":
        self._prevent_default = preventDefault
        self._stop_propogation = stopPropagation
        return self

    def add(self, function: _EHF, using: Optional[str] = None) -> "EventHandler":
        """Add a callback to the event handler.

        Parameters:
            function:
                The event handler function. Its parameters may indicate event attributes
                which should be sent back from the fronend unless otherwise specified by
                the ``using`` parameter.
            using:
                A semi-colon seperated string defining what event attribute a parameter
                refers to if the parameter name does not already refer to it directly. For
                example, accessing the current value of an ``<input/>`` element might be
                done by specifying ``using="param=target.value"``.
        """
        props_to_params: Dict[str, str] = {}
        for target_key, param in inspect.signature(function).parameters.items():
            if param.kind in (
                inspect.Parameter.VAR_POSITIONAL,
                inspect.Parameter.VAR_KEYWORD,
            ):
                raise TypeError(
                    f"Event handler {function} has variable keyword or positional arguments."
                )
            if param.default is inspect.Parameter.empty:
                props_to_params.setdefault(target_key, target_key)
        if using is not None:
            for part in map(str.strip, using.split(";")):
                target_key, source_prop = tuple(map(str.strip, part.split("=")))
                props_to_params[source_prop] = target_key
                try:
                    props_to_params.pop(target_key)
                except KeyError:
                    raise TypeError(
                        f"Event handler {function} has no parameter {target_key!r}."
                    )
        self._handler_info.append((function, props_to_params))
        return self

    def remove(self, function: _EHF) -> None:
        """Remove the function from the event handler.

        Raises:
            ValueError: if not found
        """
        for i, (f, _) in enumerate(self._handler_info):
            if f == function:
                del self._handler_info[i]
                break
        else:
            raise ValueError(f"No handler {function} exists")

    async def __call__(self, data: Dict[str, Any]) -> Any:
        """Trigger all callbacks in the event handler."""
        for handler, props_to_params in self._handler_info:
            arguments = {}
            for prop, param in props_to_params.items():
                try:
                    arguments[param] = data[prop]
                except KeyError:
                    raise ValueError(f"Event data has no {prop!r}")
            await handler(**arguments)

    def serialize(self) -> Dict[str, Any]:
        """Serialize the event handler."""
        return {
            "target": self._target_id,
            "eventProps": list(self._all_props()),
            "preventDefault": self._prevent_default,
            "stopPropagation": self._stop_propogation,
        }

    def _all_props(self) -> Set[str]:
        all_props: Set[str] = set()
        for _, props_to_params in self._handler_info:
            all_props.update(props_to_params.keys())
        return all_props

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.serialize()})"
