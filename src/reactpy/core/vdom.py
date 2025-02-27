# pyright: reportIncompatibleMethodOverride=false
from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from typing import (
    Any,
    Callable,
    cast,
    overload,
)

from fastjsonschema import compile as compile_json_schema
from typing_extensions import Unpack

from reactpy._warnings import warn
from reactpy.config import REACTPY_CHECK_JSON_ATTRS, REACTPY_DEBUG
from reactpy.core._f_back import f_module_name
from reactpy.core.events import EventHandler, to_event_handler_function
from reactpy.types import (
    ComponentType,
    CustomVdomConstructor,
    EllipsisRepr,
    EventHandlerDict,
    EventHandlerType,
    VdomAttributes,
    VdomChildren,
    VdomDict,
    VdomJson,
    VdomTypeDict,
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
_COMPILED_VDOM_VALIDATOR: Callable = compile_json_schema(VDOM_JSON_SCHEMA)  # type: ignore


def validate_vdom_json(value: Any) -> VdomJson:
    """Validate serialized VDOM - see :attr:`VDOM_JSON_SCHEMA` for more info"""
    _COMPILED_VDOM_VALIDATOR(value)
    return cast(VdomJson, value)


def is_vdom(value: Any) -> bool:
    """Return whether a value is a :class:`VdomDict`"""
    return isinstance(value, VdomDict)


class Vdom:
    """Class that follows VDOM spec, and exposes the user API that can create VDOM elements."""

    def __init__(
        self,
        /,
        allow_children: bool = True,
        custom_constructor: CustomVdomConstructor | None = None,
        **kwargs: Unpack[VdomTypeDict],
    ) -> None:
        """`**kwargs` provided here are considered as defaults for dictionary key values.
        Other arguments exist to configure the way VDOM dictionaries are constructed."""
        if "tagName" not in kwargs:
            msg = "You must specify a 'tagName' for a VDOM element."
            raise ValueError(msg)
        self.allow_children = allow_children
        self.custom_constructor = custom_constructor
        self.default_values = kwargs

        # Configure Python debugger attributes
        self.__name__ = kwargs["tagName"]
        module_name = f_module_name(1)
        if module_name:
            self.__module__ = module_name
            self.__qualname__ = f"{module_name}.{kwargs['tagName']}"

    @overload
    def __call__(
        self, attributes: VdomAttributes, /, *children: VdomChildren
    ) -> VdomDict: ...

    @overload
    def __call__(self, *children: VdomChildren) -> VdomDict: ...

    def __call__(
        self, *attributes_and_children: VdomAttributes | VdomChildren
    ) -> VdomDict:
        """The entry point for the VDOM API, for example reactpy.html(<WE_ARE_HERE>)."""
        attributes, children = separate_attributes_and_children(attributes_and_children)
        key = attributes.pop("key", None)
        attributes, event_handlers = separate_attributes_and_event_handlers(attributes)
        if REACTPY_CHECK_JSON_ATTRS.current:
            json.dumps(attributes)

        # Run custom constructor, if defined
        if self.custom_constructor:
            result = self.custom_constructor(
                key=key,
                children=children,
                attributes=attributes,
                event_handlers=event_handlers,
            )
        # Otherwise, use the default constructor
        else:
            result = {
                **({"key": key} if key is not None else {}),
                **({"children": children} if children else {}),
                **({"attributes": attributes} if attributes else {}),
                **({"eventHandlers": event_handlers} if event_handlers else {}),
            }

        # Validate the result
        if children and not self.allow_children:
            msg = f"{self.default_values.get('tagName')!r} nodes cannot have children."
            raise TypeError(msg)

        return VdomDict(**(self.default_values | result))  # type: ignore


def separate_attributes_and_children(
    values: Sequence[Any],
) -> tuple[VdomAttributes, list[Any]]:
    if not values:
        return {}, []

    _attributes: VdomAttributes
    children_or_iterables: Sequence[Any]
    # ruff: noqa: E721
    if type(values[0]) is dict:
        _attributes, *children_or_iterables = values
    else:
        _attributes = {}
        children_or_iterables = values

    _children: list[Any] = _flatten_children(children_or_iterables)

    return _attributes, _children


def separate_attributes_and_event_handlers(
    attributes: Mapping[str, Any],
) -> tuple[VdomAttributes, EventHandlerDict]:
    _attributes: VdomAttributes = {}
    _event_handlers: dict[str, EventHandlerType] = {}

    for k, v in attributes.items():
        handler: EventHandlerType

        if callable(v):
            handler = EventHandler(to_event_handler_function(v))
        elif isinstance(v, EventHandler):
            handler = v
        else:
            _attributes[k] = v
            continue

        _event_handlers[k] = handler

    return _attributes, _event_handlers


def _flatten_children(children: Sequence[Any]) -> list[Any]:
    _children: list[VdomChildren] = []
    for child in children:
        if _is_single_child(child):
            _children.append(child)
        else:
            _children.extend(_flatten_children(child))
    return _children


def _is_single_child(value: Any) -> bool:
    if isinstance(value, (str, Mapping)) or not hasattr(value, "__iter__"):
        return True
    if REACTPY_DEBUG.current:
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
                child_copy = {**child, "children": EllipsisRepr()}
                warn(f"Key not specified for child in list {child_copy}", UserWarning)
