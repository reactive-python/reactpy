import inspect
from typing import Mapping, Dict, TypeVar, Callable, Any, Optional, Iterator

from .utils import bound_id


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
