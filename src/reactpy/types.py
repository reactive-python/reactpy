"""Exports common types from:

- :mod:`reactpy.core.types`
- :mod:`reactpy.backend.types`
"""

from reactpy.core.component import Component
from reactpy.core.types import (
    ComponentConstructor,
    ComponentType,
    Connection,
    Context,
    EventHandlerDict,
    EventHandlerFunc,
    EventHandlerMapping,
    EventHandlerType,
    ImportSourceDict,
    Key,
    LayoutType,
    Location,
    RootComponentConstructor,
    State,
    VdomAttributes,
    VdomChild,
    VdomChildren,
    VdomDict,
    VdomJson,
)

__all__ = [
    "Component",
    "ComponentConstructor",
    "ComponentType",
    "Connection",
    "Context",
    "EventHandlerDict",
    "EventHandlerFunc",
    "EventHandlerMapping",
    "EventHandlerType",
    "ImportSourceDict",
    "Key",
    "LayoutType",
    "Location",
    "RootComponentConstructor",
    "State",
    "VdomAttributes",
    "VdomChild",
    "VdomChildren",
    "VdomDict",
    "VdomJson",
]
