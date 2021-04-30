"""
VDOM Constructors
=================
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple, Union

from fastjsonschema import compile as compile_json_schema
from mypy_extensions import TypedDict
from typing_extensions import Protocol

from .events import EventHandler


VDOM_JSON_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema",
    "$ref": "#/definitions/element",
    "definitions": {
        "element": {
            "type": "object",
            "properties": {
                "tagName": {"type": "string"},
                "key": {"type": "string"},
                "children": {"$ref": "#/definitions/elementChildren"},
                "attributes": {"type": "object"},
                "eventHandlers": {"$ref": "#/definitions/elementEventHandlers"},
                "importSource": {"$ref": "#/definitions/importSource"},
            },
            "required": ["tagName"],
        },
        "elementChildren": {
            "type": "array",
            "items": {"$ref": "#/definitions/elementOrString"},
        },
        "elementEventHandlers": {
            "type": "object",
            "patternProperties": {
                ".*": {"$ref": "#/definitions/eventHander"},
            },
        },
        "eventHander": {
            "type": "object",
            "properties": {
                "target": {"type": "string"},
                "preventDefault": {"type": "boolean"},
                "stopPropagation": {"type": "boolean"},
            },
            "required": ["target"],
        },
        "importSource": {
            "type": "object",
            "properties": {
                "source": {"type": "string"},
                "fallback": {
                    "type": ["object", "string", "null"],
                    "if": {"not": {"type": "null"}},
                    "then": {"$ref": "#/definitions/elementOrString"},
                },
            },
            "required": ["source"],
        },
        "elementOrString": {
            "type": ["object", "string"],
            "if": {"type": "object"},
            "then": {"$ref": "#/definitions/element"},
        },
    },
}
"""JSON Schema describing serialized VDOM - see :ref:`VDOM Mimetype` for more info"""


# we can't add a docstring to this because Sphinx doesn't know how to find its source
_COMPILED_VDOM_VALIDATOR = compile_json_schema(VDOM_JSON_SCHEMA)


def validate_vdom(value: Any) -> None:
    """Validate serialized VDOM - see :attr:`VDOM_JSON_SCHEMA` for more info"""
    _COMPILED_VDOM_VALIDATOR(value)


class ImportSourceDict(TypedDict):
    source: str
    fallback: Any


class _VdomDictOptional(TypedDict, total=False):
    key: str  # noqa
    children: Sequence[Any]  # noqa
    attributes: Mapping[str, Any]  # noqa
    eventHandlers: Mapping[str, EventHandler]  # noqa
    importSource: ImportSourceDict  # noqa


class _VdomDictRequired(TypedDict, total=True):
    tagName: str  # noqa


class VdomDict(_VdomDictRequired, _VdomDictOptional):
    """A VDOM dictionary"""


_AttributesAndChildrenArg = Union[Mapping[str, Any], str, Iterable[Any], Any]
_EventHandlersArg = Optional[Mapping[str, EventHandler]]
_ImportSourceArg = Optional[ImportSourceDict]


def vdom(
    tag: str,
    *attributes_and_children: _AttributesAndChildrenArg,
    key: str = "",
    event_handlers: _EventHandlersArg = None,
    import_source: _ImportSourceArg = None,
) -> VdomDict:
    """A helper function for creating VDOM dictionaries.

    Parameters:
        tag:
            The type of element (e.g. 'div', 'h1', 'img')
        attributes_and_children:
            Attribute mappings followed by iterables of children for the element. The
            attributes **must** precede the children, though you may pass multiple sets
            of attributes, or children which will be merged into their respective parts
            of the model.
        key:
            A string idicating the identity of a particular element. This is significant
            to preserve event handlers across updates - without a key, a re-render would
            cause these handlers to be deleted, but with a key, they would be redirected
            to any newly defined handlers.
        event_handlers:
            Maps event types to coroutines that are responsible for handling those events.
        import_source:
            (subject to change) specifies javascript that, when evaluated returns a
            React component.
    """
    model: VdomDict = {"tagName": tag}

    attributes, children = coalesce_attributes_and_children(attributes_and_children)

    if attributes:
        model["attributes"] = attributes

    if children:
        model["children"] = children

    if key:
        model["key"] = key

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
        key: str = "",
        event_handlers: _EventHandlersArg = None,
        import_source: _ImportSourceArg = None,
    ) -> VdomDict:
        model = vdom(
            tag,
            *attributes_and_children,
            key=key,
            event_handlers=event_handlers,
            import_source=import_source,
        )
        if not allow_children and "children" in model:
            raise TypeError(f"{tag!r} nodes cannot have children.")
        return model

    constructor.__name__ = tag
    qualname_prefix = constructor.__qualname__.rsplit(".", 1)[0]
    constructor.__qualname__ = qualname_prefix + f".{tag}"
    constructor.__doc__ = (
        f"""Create a new ``<{tag}/>`` - returns :ref:`VDOM <VDOM Mimetype>`."""
    )

    return constructor


def coalesce_attributes_and_children(
    attributes_and_children: _AttributesAndChildrenArg,
) -> Tuple[Dict[str, Any], List[Any]]:
    attributes: Dict[str, Any] = {}
    children: List[Any] = []

    began_children = False
    for argument in attributes_and_children:
        if isinstance(argument, Mapping):
            if "tagName" not in argument:
                if began_children:
                    raise ValueError("Attribute dictionaries should precede children.")
                attributes.update(argument)
            else:
                children.append(argument)
                began_children = True
        elif not isinstance(argument, str) and isinstance(argument, Iterable):
            children.extend(argument)
            began_children = True
        else:
            children.append(argument)
            began_children = True

    return attributes, children
