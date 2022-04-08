"""Exports common types from:

- :mod:`idom.core.types`
- :mod:`idom.server.types`
"""

from .backend.types import Location, ServerImplementation
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
    VdomAttributes,
    VdomAttributesAndChildren,
    VdomChild,
    VdomChildren,
    VdomDict,
    VdomJson,
)


__all__ = [
    "ComponentConstructor",
    "ComponentType",
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
    "VdomAttributes",
    "VdomAttributesAndChildren",
    "VdomChild",
    "VdomChildren",
    "VdomDict",
    "VdomJson",
    "ServerImplementation",
]
