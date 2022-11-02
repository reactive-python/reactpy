"""Exports common types from:

- :mod:`idom.core.types`
- :mod:`idom.backend.types`
"""

from .backend.types import BackendImplementation, Connection, Location
from .core.component import Component
from .core.hooks import Context
from .core.types import (
    ComponentConstructor,
    ComponentType,
    EventHandlerDict,
    EventHandlerFunc,
    EventHandlerMapping,
    EventHandlerType,
    ImportSourceDict,
    Key,
    LayoutType,
    RootComponentConstructor,
    State,
    VdomAttributes,
    VdomAttributesAndChildren,
    VdomChild,
    VdomChildren,
    VdomDict,
    VdomJson,
)


__all__ = [
    "BackendImplementation",
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
    "VdomAttributesAndChildren",
    "VdomChild",
    "VdomChildren",
    "VdomDict",
    "VdomJson",
]
