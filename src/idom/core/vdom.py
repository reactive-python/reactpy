"""
VDOM Constructors
=================
"""

from __future__ import annotations

import inspect
import logging
from typing import Any, Iterable, List, Mapping, Optional, Sequence, Tuple, Union

from fastjsonschema import compile as compile_json_schema
from mypy_extensions import TypedDict
from typing_extensions import Protocol

from idom.config import IDOM_DEBUG_MODE

from .events import EventHandler


logger = logging.getLogger()


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
                "sourceType": {"enum": ["URL", "NAME"]},
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
    sourceType: str  # noqa


class _VdomDictOptional(TypedDict, total=False):
    key: str  # noqa
    children: Sequence[Any]  # noqa
    attributes: Mapping[str, Any]  # noqa
    eventHandlers: Mapping[str, EventHandler]  # noqa
    importSource: ImportSourceDict  # noqa


class _VdomDictRequired(TypedDict, total=True):
    tagName: str  # noqa


class VdomDict(_VdomDictRequired, _VdomDictOptional):
    """A VDOM dictionary - see :ref:`VDOM Mimetype` for more info"""


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
            An optional attribute mapping followed by any number of children or
            iterables of children. The attribute mapping **must** precede the children,
            or children which will be merged into their respective parts of the model.
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

    # replicate common function attributes
    constructor.__name__ = tag
    constructor.__doc__ = f"Return a new ``<{tag}/>`` :class:`VdomDict` element"

    frame = inspect.currentframe()
    if frame is not None and frame.f_back is not None and frame.f_back is not None:
        module = frame.f_back.f_globals.get("__name__")  # module in outer frame
        if module is not None:
            qualname = module + "." + tag
            constructor.__module__ = module
            constructor.__qualname__ = qualname

    return constructor


def coalesce_attributes_and_children(
    values: Sequence[Any],
) -> Tuple[Mapping[str, Any], List[Any]]:
    if not values:
        return {}, []

    children_or_iterables: Sequence[Any]
    attributes, *children_or_iterables = values
    if not _is_attributes(attributes):
        attributes = {}
        children_or_iterables = values

    children: List[Any] = []
    for child in children_or_iterables:
        if _is_single_child(child):
            children.append(child)
        else:
            children.extend(child)

    return attributes, children


def _is_attributes(value: Any) -> bool:
    return isinstance(value, Mapping) and "tagName" not in value


if IDOM_DEBUG_MODE.current:

    _debug_is_attributes = _is_attributes

    def _is_attributes(value: Any) -> bool:
        result = _debug_is_attributes(value)
        if result and "children" in value:
            logger.error(f"Reserved key 'children' found in attributes {value}")
        return result


def _is_single_child(value: Any) -> bool:
    return isinstance(value, (str, Mapping)) or not hasattr(value, "__iter__")


if IDOM_DEBUG_MODE.current:

    _debug_is_single_child = _is_single_child

    def _is_single_child(value: Any) -> bool:
        if _debug_is_single_child(value):
            return True

        from .component import ComponentType

        if hasattr(value, "__iter__") and not hasattr(value, "__len__"):
            logger.error(
                f"Did not verify key-path integrity of children in generator {value} "
                "- pass a sequence (i.e. list of finite length) in order to verify"
            )
        else:
            for child in value:
                if (isinstance(child, ComponentType) and child.key is None) or (
                    isinstance(child, Mapping) and "key" not in child
                ):
                    logger.error(f"Key not specified for dynamic child {child}")

        return False
