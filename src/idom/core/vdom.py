from __future__ import annotations

import logging
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple, cast

from fastjsonschema import compile as compile_json_schema
from typing_extensions import Protocol

from idom.config import IDOM_DEBUG_MODE
from idom.core.events import (
    EventHandler,
    merge_event_handlers,
    to_event_handler_function,
)
from idom.core.types import (
    EventHandlerDict,
    EventHandlerMapping,
    EventHandlerType,
    ImportSourceDict,
    VdomAttributesAndChildren,
    VdomDict,
    VdomJson,
)

from ._f_back import f_module_name


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
                "error": {"type": "string"},
                "children": {"$ref": "#/definitions/elementChildren"},
                "attributes": {"type": "object"},
                "eventHandlers": {"$ref": "#/definitions/elementEventHandlers"},
                "importSource": {"$ref": "#/definitions/importSource"},
            },
            # The 'tagName' is required because its presence is a useful indicator of
            # whether a dictionary describes a VDOM model or not.
            "required": ["tagName"],
            "dependentSchemas": {
                # When 'error' is given, the 'tagName' should be empty.
                "error": {"properties": {"tagName": {"maxLength": 0}}}
            },
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
                "unmountBeforeUpdate": {"type": "boolean"},
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
"""JSON Schema describing serialized VDOM - see :ref:`VDOM` for more info"""


# we can't add a docstring to this because Sphinx doesn't know how to find its source
_COMPILED_VDOM_VALIDATOR = compile_json_schema(VDOM_JSON_SCHEMA)


def validate_vdom_json(value: Any) -> VdomJson:
    """Validate serialized VDOM - see :attr:`VDOM_JSON_SCHEMA` for more info"""
    _COMPILED_VDOM_VALIDATOR(value)
    return cast(VdomJson, value)


def is_vdom(value: Any) -> bool:
    """Return whether a value is a :class:`VdomDict`

    This employs a very simple heuristic - something is VDOM if:

    1. It is a ``dict`` instance
    2. It contains the key ``"tagName"``
    3. The value of the key ``"tagName"`` is a string

    .. note::

        Performing an ``isinstance(value, VdomDict)`` check is too restrictive since the
        user would be forced to import ``VdomDict`` every time they needed to declare a
        VDOM element. Giving the user more flexibility, at the cost of this check's
        accuracy, is worth it.
    """
    return (
        isinstance(value, dict)
        and "tagName" in value
        and isinstance(value["tagName"], str)
    )


def vdom(
    tag: str,
    *attributes_and_children: VdomAttributesAndChildren,
    key: str | int | None = None,
    event_handlers: Optional[EventHandlerMapping] = None,
    import_source: Optional[ImportSourceDict] = None,
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
    attributes, event_handlers = separate_attributes_and_event_handlers(
        attributes, event_handlers or {}
    )

    if attributes:
        model["attributes"] = attributes

    if children:
        model["children"] = children

    if event_handlers:
        model["eventHandlers"] = event_handlers

    if key is not None:
        model["key"] = key

    if import_source is not None:
        model["importSource"] = import_source

    return model


class _VdomDictConstructor(Protocol):
    def __call__(
        self,
        *attributes_and_children: VdomAttributesAndChildren,
        key: str | int | None = ...,
        event_handlers: Optional[EventHandlerMapping] = ...,
        import_source: Optional[ImportSourceDict] = ...,
    ) -> VdomDict:
        ...


def make_vdom_constructor(
    tag: str, allow_children: bool = True
) -> _VdomDictConstructor:
    """Return a constructor for VDOM dictionaries with the given tag name.

    The resulting callable will have the same interface as :func:`vdom` but without its
    first ``tag`` argument.
    """

    def constructor(
        *attributes_and_children: VdomAttributesAndChildren,
        key: str | int | None = None,
        event_handlers: Optional[EventHandlerMapping] = None,
        import_source: Optional[ImportSourceDict] = None,
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
    constructor.__doc__ = (
        "Return a new "
        f"`<{tag}> <https://developer.mozilla.org/en-US/docs/Web/HTML/Element/{tag}>`__ "
        "element represented by a :class:`VdomDict`."
    )

    module_name = f_module_name(1)
    if module_name:
        constructor.__module__ = module_name
        constructor.__qualname__ = f"{module_name}.{tag}"

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


def separate_attributes_and_event_handlers(
    attributes: Mapping[str, Any], event_handlers: EventHandlerMapping
) -> Tuple[Dict[str, Any], EventHandlerDict]:
    separated_attributes = {}
    separated_event_handlers: Dict[str, List[EventHandlerType]] = {}

    for k, v in event_handlers.items():
        separated_event_handlers[k] = [v]

    for k, v in attributes.items():

        handler: EventHandlerType

        if callable(v):
            handler = EventHandler(to_event_handler_function(v))
        elif (
            # isinstance check on protocols is slow, function attr check is a quick filter
            hasattr(v, "function")
            and isinstance(v, EventHandlerType)
        ):
            handler = v
        else:
            separated_attributes[k] = v
            continue

        if k not in separated_event_handlers:
            separated_event_handlers[k] = [handler]
        else:
            separated_event_handlers[k].append(handler)

    flat_event_handlers_dict = {
        k: merge_event_handlers(h) for k, h in separated_event_handlers.items()
    }

    return separated_attributes, flat_event_handlers_dict


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

        from .types import ComponentType

        if hasattr(value, "__iter__") and not hasattr(value, "__len__"):
            logger.error(
                f"Did not verify key-path integrity of children in generator {value} "
                "- pass a sequence (i.e. list of finite length) in order to verify"
            )
        else:
            for child in value:
                if isinstance(child, ComponentType) and child.key is None:
                    logger.error(f"Key not specified for child in list {child}")
                elif isinstance(child, Mapping) and "key" not in child:
                    # remove 'children' to reduce log spam
                    child_copy = {**child, "children": _EllipsisRepr()}
                    logger.error(f"Key not specified for child in list {child_copy}")

        return False

    class _EllipsisRepr:
        def __repr__(self) -> str:
            return "..."
