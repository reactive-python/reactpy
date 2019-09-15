from typing import Optional, Iterable, Any, Dict, List, Tuple, Union

from mypy_extensions import TypedDict
from typing_extensions import Protocol

from .events import EventsMapping


class ImportSourceDict(TypedDict):
    source: str
    fallback: Any


class VdomDict(TypedDict, total=False):
    tagName: Optional[str]
    children: Union[List[Any], Tuple[Any, ...]]
    attributes: Dict[str, Any]
    eventHandlers: EventsMapping
    importSource: ImportSourceDict


_TagArg = Optional[str]
_ChildrenOrAttributesArg = Union[Dict[str, Any], Iterable[Any]]
_EventHandlersArg = Optional[EventsMapping]
_ImportSourceArg = Optional[ImportSourceDict]


def node(
    tag: _TagArg,
    *args: _ChildrenOrAttributesArg,
    event_handlers: _EventHandlersArg = None,
    import_source: _ImportSourceArg = None,
) -> VdomDict:
    """A helper function for generating DOM model dictionaries."""
    model: VdomDict = {"tagName": tag}
    attributes: Dict[str, Any] = {}
    children: List[Any] = []

    for argument in args:
        if isinstance(argument, dict):
            attributes.update(argument)
        else:
            children.extend(argument)

    if attributes:
        model["attributes"] = attributes

    if children:
        model["children"] = children

    if event_handlers:
        model["eventHandlers"] = event_handlers

    if import_source:
        model["importSource"] = import_source

    return model


class _NodeConstructor(Protocol):
    def __call__(
        self,
        *args: _ChildrenOrAttributesArg,
        event_handlers: _EventHandlersArg = None,
        import_source: _ImportSourceArg = None,
    ) -> VdomDict:
        ...


def node_constructor(tag: str, allow_children: bool = True) -> _NodeConstructor:
    """Create a constructor for nodes with the given tag name."""

    def constructor(
        *args: _ChildrenOrAttributesArg,
        event_handlers: _EventHandlersArg = None,
        import_source: _ImportSourceArg = None,
    ) -> VdomDict:
        model = node(
            tag, *args, event_handlers=event_handlers, import_source=import_source
        )
        if not allow_children and "children" in model:
            raise TypeError(f"{tag!r} nodes cannot have children.")
        return model

    constructor.__name__ = tag
    qualname_prefix = constructor.__qualname__.rsplit(".", 1)[0]
    constructor.__qualname__ = qualname_prefix + f".{tag}"
    constructor.__doc__ = f"""Create a new ``<{tag}/>`` - returns :term:`VDOM`."""

    return constructor
