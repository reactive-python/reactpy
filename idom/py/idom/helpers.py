from collections.abc import Mapping

from typing import Any, Callable, Dict, Optional

from .utils import Bunch


def snake_to_camel(string):
    return "".join(part[:1].upper() + part[1:] for part in string.split("_"))


def node(tag: str, *children: Any, **attributes: Any) -> "Node":
    if len(children) == 1:
        if isinstance(children[0], (list, tuple)):
            children = tuple(children[0])
    event_handlers = attributes.pop("eventHandlers", Events())
    attributes.setdefault("style", {})
    return Node(
        {
            "tagName": tag,
            "children": children,
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

    def on(self, event: str) -> Callable:
        event_name = "on" + snake_to_camel(event)

        def setup(function: Callable) -> Callable:
            self._handlers[event_name] = function
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
