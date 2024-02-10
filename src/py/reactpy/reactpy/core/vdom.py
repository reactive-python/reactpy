from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from functools import wraps
from typing import Any, Protocol, cast, overload

from fastjsonschema import compile as compile_json_schema

from reactpy._warnings import warn
from reactpy.config import REACTPY_CHECK_JSON_ATTRS, REACTPY_DEBUG_MODE
from reactpy.core._f_back import f_module_name
from reactpy.core.events import EventHandler, to_event_handler_function
from reactpy.core.types import (
    ComponentType,
    EventHandlerDict,
    EventHandlerType,
    ImportSourceDict,
    Key,
    VdomAttributes,
    VdomChild,
    VdomChildren,
    VdomDict,
    VdomDictConstructor,
    VdomJson,
)

VDOM_JSON_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema",
    "$ref": "#/definitions/element",
    "definitions": {
        "element": {
            "type": "object",
            "properties": {
                "tagName": {"type": "string"},
                "key": {"type": ["string", "number", "null"]},
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
                ".*": {"$ref": "#/definitions/eventHandler"},
            },
        },
        "eventHandler": {
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


@overload
def vdom(tag: str, *children: VdomChildren) -> VdomDict: ...


@overload
def vdom(tag: str, attributes: VdomAttributes, *children: VdomChildren) -> VdomDict: ...


def vdom(
    tag: str,
    *attributes_and_children: Any,
    **kwargs: Any,
) -> VdomDict:
    """A helper function for creating VDOM elements.

    Parameters:
        tag:
            The type of element (e.g. 'div', 'h1', 'img')
        attributes_and_children:
            An optional attribute mapping followed by any number of children or
            iterables of children. The attribute mapping **must** precede the children,
            or children which will be merged into their respective parts of the model.
        key:
            A string indicating the identity of a particular element. This is significant
            to preserve event handlers across updates - without a key, a re-render would
            cause these handlers to be deleted, but with a key, they would be redirected
            to any newly defined handlers.
        event_handlers:
            Maps event types to coroutines that are responsible for handling those events.
        import_source:
            (subject to change) specifies javascript that, when evaluated returns a
            React component.
    """
    if kwargs:  # nocov
        if "key" in kwargs:
            if attributes_and_children:
                maybe_attributes, *children = attributes_and_children
                if _is_attributes(maybe_attributes):
                    attributes_and_children = (
                        {**maybe_attributes, "key": kwargs.pop("key")},
                        *children,
                    )
                else:
                    attributes_and_children = (
                        {"key": kwargs.pop("key")},
                        maybe_attributes,
                        *children,
                    )
            else:
                attributes_and_children = ({"key": kwargs.pop("key")},)
            warn(
                "An element's 'key' must be declared in an attribute dict instead "
                "of as a keyword argument. This will error in a future version.",
                DeprecationWarning,
            )

        if kwargs:
            msg = f"Extra keyword arguments {kwargs}"
            raise ValueError(msg)

    model: VdomDict = {"tagName": tag}

    if not attributes_and_children:
        return model

    attributes, children = separate_attributes_and_children(attributes_and_children)
    key = attributes.pop("key", None)
    attributes, event_handlers = separate_attributes_and_event_handlers(attributes)

    if attributes:
        if REACTPY_CHECK_JSON_ATTRS.current:
            json.dumps(attributes)
        model["attributes"] = attributes

    if children:
        model["children"] = children

    if key is not None:
        model["key"] = key

    if event_handlers:
        model["eventHandlers"] = event_handlers

    return model


def make_vdom_constructor(
    tag: str, allow_children: bool = True, import_source: ImportSourceDict | None = None
) -> VdomDictConstructor:
    """Return a constructor for VDOM dictionaries with the given tag name.

    The resulting callable will have the same interface as :func:`vdom` but without its
    first ``tag`` argument.
    """

    def constructor(*attributes_and_children: Any, **kwargs: Any) -> VdomDict:
        model = vdom(tag, *attributes_and_children, **kwargs)
        if not allow_children and "children" in model:
            msg = f"{tag!r} nodes cannot have children."
            raise TypeError(msg)
        if import_source:
            model["importSource"] = import_source
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

    return cast(VdomDictConstructor, constructor)


def custom_vdom_constructor(func: _CustomVdomDictConstructor) -> VdomDictConstructor:
    """Cast function to VdomDictConstructor"""

    @wraps(func)
    def wrapper(*attributes_and_children: Any) -> VdomDict:
        attributes, children = separate_attributes_and_children(attributes_and_children)
        key = attributes.pop("key", None)
        attributes, event_handlers = separate_attributes_and_event_handlers(attributes)
        return func(attributes, children, key, event_handlers)

    return cast(VdomDictConstructor, wrapper)


def separate_attributes_and_children(
    values: Sequence[Any],
) -> tuple[dict[str, Any], list[Any]]:
    if not values:
        return {}, []

    attributes: dict[str, Any]
    children_or_iterables: Sequence[Any]
    if _is_attributes(values[0]):
        attributes, *children_or_iterables = values
    else:
        attributes = {}
        children_or_iterables = values

    children: list[Any] = []
    for child in children_or_iterables:
        if _is_single_child(child):
            children.append(child)
        else:
            children.extend(child)

    return attributes, children


def separate_attributes_and_event_handlers(
    attributes: Mapping[str, Any]
) -> tuple[dict[str, Any], EventHandlerDict]:
    separated_attributes = {}
    separated_event_handlers: dict[str, EventHandlerType] = {}

    for k, v in attributes.items():
        handler: EventHandlerType

        if callable(v):
            handler = EventHandler(to_event_handler_function(v))
        elif (
            # isinstance check on protocols is slow - use function attr pre-check as a
            # quick filter before actually performing slow EventHandlerType type check
            hasattr(v, "function")
            and isinstance(v, EventHandlerType)
        ):
            handler = v
        else:
            separated_attributes[k] = v
            continue

        separated_event_handlers[k] = handler

    return separated_attributes, dict(separated_event_handlers.items())


def _is_attributes(value: Any) -> bool:
    return isinstance(value, Mapping) and "tagName" not in value


def _is_single_child(value: Any) -> bool:
    if isinstance(value, (str, Mapping)) or not hasattr(value, "__iter__"):
        return True
    if REACTPY_DEBUG_MODE.current:
        _validate_child_key_integrity(value)
    return False


def _validate_child_key_integrity(value: Any) -> None:
    if hasattr(value, "__iter__") and not hasattr(value, "__len__"):
        warn(
            f"Did not verify key-path integrity of children in generator {value} "
            "- pass a sequence (i.e. list of finite length) in order to verify"
        )
    else:
        for child in value:
            if isinstance(child, ComponentType) and child.key is None:
                warn(f"Key not specified for child in list {child}", UserWarning)
            elif isinstance(child, Mapping) and "key" not in child:
                # remove 'children' to reduce log spam
                child_copy = {**child, "children": _EllipsisRepr()}
                warn(f"Key not specified for child in list {child_copy}", UserWarning)


class _CustomVdomDictConstructor(Protocol):
    def __call__(
        self,
        attributes: VdomAttributes,
        children: Sequence[VdomChild],
        key: Key | None,
        event_handlers: EventHandlerDict,
    ) -> VdomDict: ...


class _EllipsisRepr:
    def __repr__(self) -> str:
        return "..."
