from typing import Optional, Iterable, Any, Dict, List, Tuple, Union, Mapping

from mypy_extensions import TypedDict
from typing_extensions import Protocol

from .events import EventsMapping


class ImportSourceDict(TypedDict):
    source: str
    fallback: Any


class VdomDict(TypedDict, total=False):  # fmt: off
    tagName: Optional[str]  # noqa
    children: Union[List[Any], Tuple[Any, ...]]  # noqa
    attributes: Dict[str, Any]  # noqa
    eventHandlers: EventsMapping  # noqa
    importSource: ImportSourceDict  # noqa


_TagArg = Optional[str]
_AttributesAndChildrenArg = Union[Mapping[str, Any], Iterable[Any]]
_EventHandlersArg = Optional[EventsMapping]
_ImportSourceArg = Optional[ImportSourceDict]


def vdom(
    tag: _TagArg,
    *attributes_and_children: _AttributesAndChildrenArg,
    event_handlers: _EventHandlersArg = None,
    import_source: _ImportSourceArg = None,
) -> VdomDict:
    """A helper function for creating VDOM dictionaries.
    Parameters:
        tag:
            The type of element (e.g. 'div', 'h1', 'img')
        attributes_and_children:
            Attribute mappings followed by iterables of children for the element.
            The attributes **must** precede the children, though you may pass multiple
            sets of attributes, or children which will be merged into their respective
            parts of the model.
        event_handlers:
            Maps event types to coroutines that are responsible for handling those events.
        import_source:
            (subject to change) specifies javascript that, when evaluated returns a
            React component.
    """
    model: VdomDict = {"tagName": tag}
    attributes: Dict[str, Any] = {}
    children: List[Any] = []

    began_children = False
    for argument in attributes_and_children:
        if isinstance(argument, dict):
            if began_children:
                raise ValueError("Attribute dictionaries should precede child lists.")
            attributes.update(argument)
        else:
            children.extend(argument)
            began_children = True

    if attributes:
        model["attributes"] = attributes

    if children:
        model["children"] = children

    if event_handlers is not None:
        model["eventHandlers"] = event_handlers

    if import_source is not None:
        model["importSource"] = import_source

    return model


class VdomDictConstructor(Protocol):
    def __call__(
        self,
        *args: _AttributesAndChildrenArg,
        event_handlers: _EventHandlersArg = None,
        import_source: _ImportSourceArg = None,
    ) -> VdomDict:
        ...


def make_vdom_constructor(tag: str, allow_children: bool = True) -> VdomDictConstructor:
    """Return a constructor for VDOM dictionaries with the given tag name.
    The resulting callable will have the same interface as :func:`vdom` but without its
    first ``tag`` argument.
    """

    def constructor(
        *attributes_and_children: _AttributesAndChildrenArg,
        event_handlers: _EventHandlersArg = None,
        import_source: _ImportSourceArg = None,
    ) -> VdomDict:
        model = vdom(
            tag,
            *attributes_and_children,
            event_handlers=event_handlers,
            import_source=import_source,
        )
        if not allow_children and "children" in model:
            raise TypeError(f"{tag!r} nodes cannot have children.")
        return model

    constructor.__name__ = tag
    qualname_prefix = constructor.__qualname__.rsplit(".", 1)[0]
    constructor.__qualname__ = qualname_prefix + f".{tag}"
    constructor.__doc__ = f"""Create a new ``<{tag}/>`` - returns :term:`VDOM`."""

    return constructor
