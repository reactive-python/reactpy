from weakref import proxy, CallableProxyType
from functools import partial
from typing import (
    Mapping,
    Dict,
    Callable,
    Any,
    Optional,
    Iterator,
    List,
    Awaitable,
    Union,
)

from .utils import bound_id
from .element import AbstractElement


EventHandlerFunction = Callable[..., Awaitable[Any]]  # event handler function


def event(
    function: Optional[EventHandlerFunction] = None,
    stopPropagation: bool = False,
    preventDefault: bool = False,
) -> Union["EventHandler", Callable[[EventHandlerFunction], "EventHandler"]]:
    """Create an event handler function with extra functionality.

    You're always free to add callbacks by assigning them to element callbacks.

    .. code-block:: python

        element = idom.html.button(onClick=my_callback)

    However you may want the ability to prevent the default action associated
    with the event from taking place, or stoping the event from propagating up
    the DOM. This decorator allows you to add that functionality to your callbacks.

    Parameters:
        function:
            A coroutine of the form ``async handler(event)`` where ``event`` is
            a dictionary of event data.
        stopPropagation:
            Block the event from propagating further up the DOM.
        preventDefault:
            Stops the default actional associate with the event from taking place.
    """
    handler = EventHandler(stopPropagation, preventDefault)
    if function is not None:
        handler.add(function)
        return handler
    else:
        return handler.add


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
        self, event: str, stopPropagation: bool = False, preventDefault: bool = False
    ) -> Callable[[EventHandlerFunction], EventHandlerFunction]:
        """A decorator for adding an event handler.

        Parameters:
            event:
                The camel-case name of the event, the word "on" is automatically
                prepended. So passing "keyDown" would refer to the event "onKeyDown".
        Returns:
            A decorator which accepts an event handler function as its first argument.
            The parameters of the event handler function may indicate event attributes
            which should be sent back from the frontend. See :class:`EventHandler` for
            more info.

        Examples:
            Simple "onClick" event handler:

            .. code-block:: python
                def clickable_element():
                    events = Events()

                    @events.on("click")
                    def handler(event):
                        # do something on a click event
                        ...

                    return idom.node("button", "hello!", eventHandlers=events)
        """
        if not event.startswith("on"):
            event_name = "on" + event[:1].upper() + event[1:]

        if event_name not in self._handlers:
            handler = EventHandler(stopPropagation, preventDefault)
            self._handlers[event_name] = handler
        else:
            handler = self._handlers[event_name]

        def setup(function: EventHandlerFunction) -> EventHandlerFunction:
            if self._bound is not None:
                function = partial(function, self._bound)
            handler.add(function)
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

    Get a serialized reference to the handler via :meth:`Handler.serialize`.

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
        "__weakref__",
        "_handlers",
        "_target_id",
        "_prevent_default",
        "_stop_propogation",
    )

    def __init__(
        self,
        stop_propagation: bool = False,
        prevent_default: bool = False,
        target_id: Optional[str] = None,
    ) -> None:
        self._handlers: List[EventHandlerFunction] = []
        self._target_id = target_id or bound_id(self)
        self._stop_propogation = stop_propagation
        self._prevent_default = prevent_default

    @property
    def id(self) -> str:
        return self._target_id

    def add(self, function: EventHandlerFunction) -> "EventHandler":
        """Add a callback to the event handler.

        Parameters:
            function:
                The event handler function. Its parameters may indicate event attributes
                which should be sent back from the fronend unless otherwise specified by
                the ``properties`` parameter.
        """
        self._handlers.append(function)
        return self

    def remove(self, function: EventHandlerFunction) -> None:
        """Remove the function from the event handler.

        Raises:
            ValueError: if not found
        """
        self._handlers.remove(function)

    async def __call__(self, data: List[Any]) -> Any:
        """Trigger all callbacks in the event handler."""
        for handler in self._handlers:
            await handler(*data)

    def serialize(self) -> Dict[str, Any]:
        """Serialize the event handler."""
        return {
            "target": self._target_id,
            "preventDefault": self._prevent_default,
            "stopPropagation": self._stop_propogation,
        }

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.serialize()})"
