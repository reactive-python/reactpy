"""Exports common types from:

- :mod:`idom.core.types`
- :mod:`idom.server.types`
"""

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
    VdomAttributes,
    VdomAttributesAndChildren,
    VdomChild,
    VdomChildren,
    VdomDict,
    VdomJson,
)
from .server.types import ServerFactory, ServerType


__all__ = [
    "ComponentConstructor",
    "ComponentType",
    "EventHandlerDict",
    "EventHandlerFunc",
    "EventHandlerMapping",
    "EventHandlerType",
    "ImportSourceDict",
    "Key",
    "LayoutType",
    "VdomAttributes",
    "VdomAttributesAndChildren",
    "VdomChild",
    "VdomChildren",
    "VdomDict",
    "VdomJson",
    "ServerFactory",
    "ServerType",
]
