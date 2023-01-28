from __future__ import annotations

import logging
from typing import Any, DefaultDict, Mapping, cast

from fastjsonschema import compile as compile_json_schema
from typing_extensions import TypeGuard

from idom._warnings import warn
from idom.config import IDOM_DEBUG_MODE
from idom.core.events import (
    EventHandler,
    merge_event_handlers,
    to_event_handler_function,
)
from idom.core.types import (
    ComponentType,
    EventHandlerDict,
    EventHandlerType,
    ImportSourceDict,
    Key,
    VdomChild,
    VdomChildren,
    VdomDict,
    VdomDictConstructor,
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
    *children: VdomChild | VdomChildren,
    key: Key | None = None,
    **attributes: Any,
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

    flattened_children: list[VdomChild] = []
    for child in children:
        if isinstance(child, dict) and "tagName" not in child:  # pragma: no cover
            warn(
                (
                    "Element constructor signatures have changed! This will be an error "
                    "in a future release. All element constructors now have the  "
                    "following usage where attributes may be snake_case keyword "
                    "arguments: "
                    "\n\n"
                    ">>> html.div(*children, key=key, **attributes) "
                    "\n\n"
                    "A CLI tool for automatically updating code to the latest API has "
                    "been provided with this release of IDOM (e.g. 'idom "
                    "update-html-usages'). However, it may not resolve all issues "
                    "arrising from this change. Start a discussion if you need help "
                    "transitioning to this new interface: "
                    "https://github.com/idom-team/idom/discussions/new?category=question"
                ),
                DeprecationWarning,
            )
            attributes.update(child)
        if _is_single_child(child):
            flattened_children.append(child)
        else:
            # FIXME: Types do not narrow in negative case of TypeGaurd
            # This cannot be fixed until there is some sort of "StrictTypeGuard".
            # See: https://github.com/python/typing/discussions/1013
            flattened_children.extend(child)  # type: ignore

    attributes, event_handlers = separate_attributes_and_event_handlers(attributes)

    if attributes:
        model["attributes"] = attributes

    if flattened_children:
        model["children"] = flattened_children

    if event_handlers:
        model["eventHandlers"] = event_handlers

    if key is not None:
        model["key"] = key

    return model


def with_import_source(element: VdomDict, import_source: ImportSourceDict) -> VdomDict:
    return {**element, "importSource": import_source}  # type: ignore


def make_vdom_constructor(
    tag: str,
    allow_children: bool = True,
    import_source: ImportSourceDict | None = None,
) -> VdomDictConstructor:
    """Return a constructor for VDOM dictionaries with the given tag name.

    The resulting callable will have the same interface as :func:`vdom` but without its
    first ``tag`` argument.
    """

    def constructor(
        *children: VdomChild | VdomChildren,
        key: Key | None = None,
        **attributes: Any,
    ) -> VdomDict:
        if not allow_children and children:
            raise TypeError(f"{tag!r} nodes cannot have children.")

        model = vdom(tag, *children, key=key, **attributes)
        if import_source is not None:
            model = with_import_source(model, import_source)

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


def separate_attributes_and_event_handlers(
    attributes: Mapping[str, Any]
) -> tuple[dict[str, Any], EventHandlerDict]:
    separated_attributes = {}
    separated_handlers: DefaultDict[str, list[EventHandlerType]] = DefaultDict(list)

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

        separated_handlers[k].append(handler)

    flat_event_handlers_dict = {
        k: merge_event_handlers(h) for k, h in separated_handlers.items()
    }

    return separated_attributes, flat_event_handlers_dict


def _is_single_child(value: Any) -> TypeGuard[VdomChild]:
    if isinstance(value, (str, Mapping)) or not hasattr(value, "__iter__"):
        return True
    if IDOM_DEBUG_MODE.current:
        _validate_child_key_integrity(value)
    return False


def _validate_child_key_integrity(value: Any) -> None:
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


class _EllipsisRepr:
    def __repr__(self) -> str:
        return "..."
