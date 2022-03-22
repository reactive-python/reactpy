"""Exports common types from:

- :mod:`idom.core.types`
- :mod:`idom.server.types`
"""

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
from .server.types import ServerImplementation


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
    "RootComponentConstructor",
    "VdomAttributes",
    "VdomAttributesAndChildren",
    "VdomChild",
    "VdomChildren",
    "VdomDict",
    "VdomJson",
    "ServerImplementation",
]
