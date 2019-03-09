import inspect
from collections.abc import Mapping
import uuid

from typing import Any, Callable, Dict, Optional

from .utils import Bunch, to_coroutine


def node(tag: str, *children: Any, **attributes: Any) -> "Node":
    _children = []
    for c in children:
        if isinstance(c, (list, tuple)):
            _children.extend(c)
        else:
            _children.append(c)
    event_handlers = attributes.pop("eventHandlers", Events())
    attributes.setdefault("style", {})
    return Node(
        {
            "tagName": tag,
            "children": _children,
            "attributes": attributes,
            "eventHandlers": event_handlers,
        }
    )


class Node(Bunch):
    def __setattr__(self, name, value):
        self[name] = value

    def __setitem__(self, name, value):
        self._data_[name] = value


class Events(Mapping):
    """A container for event handlers.

    Assign this object to the ``"eventHandlers"`` field of an element model.
    """

    __slots__ = "_handlers"

    def __init__(self):
        self._handlers = {}

    def on(self, event: str, where: str = None) -> Callable:
        event_name = "on" + event[:1].upper() + event[1:]

        def setup(function: Callable) -> Callable:
            self._handlers[event_name] = EventHandler(function, event_name, where)
            return function

        return setup

    def copy(self) -> "Events":
        new = Events()
        new._handlers = self._handlers
        return new

    def __len__(self):
        return len(self._handlers)

    def __iter__(self):
        return iter(self._handlers)

    def __getitem__(self, key):
        return self._handlers[key]

    def __repr__(self):
        return repr(self._handlers)


class EventHandler:

    __slots__ = ("_handler", "_event_name", "_id", "_props_to_params")

    def __init__(self, function: Callable, event_name: str, where: str = None):
        self._handler = to_coroutine(function)
        self._id = uuid.uuid1().hex
        self._event_name = event_name
        self._props_to_params: Dict[str, str] = {}
        if where is not None:
            for part in map(str.strip, where.split(",")):
                target_key, source_prop = tuple(map(str.strip, part.split("=")))
                self._props_to_params[source_prop] = target_key
        for target_key in inspect.signature(function).parameters:
            self._props_to_params.setdefault(target_key, target_key)

    async def __call__(self, data):
        data = {self._props_to_params[k]: v for k, v in data.items()}
        return (await self._handler(**data))

    def serialize(self):
        return f"{self._id}_{self._event_name}_{';'.join(self._props_to_params.keys())}"
