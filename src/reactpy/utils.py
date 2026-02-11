from __future__ import annotations

import re
from collections.abc import Callable, Iterable
from importlib import import_module
from itertools import chain
from typing import Any, Generic, TypeVar, cast

from lxml import etree
from lxml.html import fromstring

from reactpy import h
from reactpy.transforms import RequiredTransforms, attributes_to_reactjs
from reactpy.types import Component, VdomDict

_RefValue = TypeVar("_RefValue")
_ModelTransform = Callable[[VdomDict], Any]
_UNDEFINED: Any = object()


class Ref(Generic[_RefValue]):
    """Hold a reference to a value

    This is used in imperative code to mutate the state of this object in order to
    incur side effects. Generally refs should be avoided if possible, but sometimes
    they are required.

    Notes:
        You can compare the contents for two ``Ref`` objects using the ``==`` operator.
    """

    __slots__ = ("current",)

    def __init__(self, initial_value: _RefValue = _UNDEFINED) -> None:
        if initial_value is not _UNDEFINED:
            self.current = initial_value
            """The present value"""

    def set_current(self, new: _RefValue) -> _RefValue:
        """Set the current value and return what is now the old value

        This is nice to use in ``lambda`` functions.
        """
        old = self.current
        self.current = new
        return old

    __hash__ = None  # type: ignore

    def __eq__(self, other: object) -> bool:
        try:
            return isinstance(other, Ref) and (other.current == self.current)
        except AttributeError:
            # attribute error occurs for uninitialized refs
            return False

    def __repr__(self) -> str:
        try:
            current = repr(self.current)
        except AttributeError:
            # attribute error occurs for uninitialized refs
            current = "<undefined>"
        return f"{type(self).__name__}({current})"


def reactpy_to_string(root: VdomDict | Component) -> str:
    """Convert a ReactPy component or `reactpy.html` element into an HTML string.

    Parameters:
        root: The ReactPy element to convert to a string.
    """
    temp_container = etree.Element("__temp__")

    if not isinstance(root, dict):
        root = component_to_vdom(root)

    _add_vdom_to_etree(temp_container, root)
    html = etree.tostring(temp_container, method="html").decode()

    # Strip out temp root <__temp__> element
    return html[10:-11]


def string_to_reactpy(
    html: str,
    *transforms: _ModelTransform,
    strict: bool = True,
    intercept_links: bool = True,
) -> VdomDict:
    """Transform HTML string into a ReactPy DOM model. ReactJS keys can be provided to HTML elements
    using a ``key=...`` attribute within your HTML tag.

    Parameters:
        html:
            The raw HTML as a string
        transforms:
            Function that takes a VDOM dictionary input and returns the new (mutated)
            VDOM in the form ``transform(old) -> new``. This function is automatically
            called on every node within the VDOM tree.
        strict:
            If ``True``, raise an exception if the HTML does not perfectly follow HTML5
            syntax.
        intercept_links:
            If ``True``, convert all anchor tags into ``<a>`` tags with an ``onClick``
            event handler that prevents the browser from navigating to the link. This is
            useful if you would rather have `reactpy-router` handle your URL navigation.
    """
    if not isinstance(html, str):
        msg = f"Expected html to be a string, not {type(html).__name__}"
        raise TypeError(msg)
    if not html.strip():
        return h.div()
    if "<" not in html or ">" not in html:
        msg = "Expected html string to contain HTML tags, but no tags were found."
        raise ValueError(msg)

    # If the user provided a string, convert it to a list of lxml.etree nodes
    try:
        root_node: etree._Element = fromstring(
            html.strip(),
            parser=etree.HTMLParser(  # type: ignore
                remove_comments=True,
                remove_pis=True,
                remove_blank_text=True,
                recover=not strict,
            ),
        )
    except Exception as e:
        msg = (
            "An error has occurred while parsing the HTML.\n\n"
            "This HTML may be malformatted, or may not adhere to the HTML5 spec.\n"
            "If you believe the exception above was due to something intentional, you "
            "can disable the strict parameter on string_to_reactpy().\n"
            "Otherwise, repair your broken HTML and try again."
        )
        raise HTMLParseError(msg) from e

    return _etree_to_vdom(root_node, transforms, intercept_links)


class HTMLParseError(etree.LxmlSyntaxError):  # type: ignore[misc]
    """Raised when an HTML document cannot be parsed using strict parsing."""


def _etree_to_vdom(
    node: etree._Element, transforms: Iterable[_ModelTransform], intercept_links: bool
) -> VdomDict:
    """Transform an lxml etree node into a DOM model."""
    if not isinstance(node, etree._Element):  # nocov
        msg = f"Expected node to be a etree._Element, not {type(node).__name__}"
        raise TypeError(msg)

    # Recursively call _etree_to_vdom() on all children
    children = _generate_vdom_children(node, transforms, intercept_links)

    # This transform is required prior to initializing the Vdom so InlineJavaScript
    # gets properly parsed (ex. <button onClick="this.innerText = 'Clicked';")
    attributes = attributes_to_reactjs(dict(node.items()))

    # Convert the lxml node to a VDOM dict
    constructor = getattr(h, str(node.tag))
    el = constructor(attributes, children)

    # Perform necessary transformations on the VDOM attributes to meet VDOM spec
    RequiredTransforms(el, intercept_links)

    # Apply any user provided transforms.
    for transform in transforms:
        el = transform(el)

    return el


def _add_vdom_to_etree(parent: etree._Element, vdom: VdomDict | dict[str, Any]) -> None:
    try:
        tag = vdom["tagName"]
    except KeyError as e:
        msg = f"Expected a VDOM dict, not {type(vdom)}"
        raise TypeError(msg) from e
    else:
        vdom = cast(VdomDict, vdom)

    if tag:
        element = etree.SubElement(parent, tag)
        element.attrib.update(
            _react_attribute_to_html(k, v)
            for k, v in vdom.get("attributes", {}).items()
        )
    else:
        element = parent

    for c in vdom.get("children", []):
        if hasattr(c, "render"):
            c = component_to_vdom(cast(Component, c))
        if isinstance(c, dict):
            _add_vdom_to_etree(element, c)

        # LXML handles string children by storing them under `text` and `tail`
        # attributes of Element objects. The `text` attribute, if present, effectively
        # becomes that element's first child. Then the `tail` attribute, if present,
        # becomes a sibling that follows that element. For example, consider the
        # following HTML:

        #     <p><a>hello</a>world</p>

        # In this code sample, "hello" is the `text` attribute of the `<a>` element
        # and "world" is the `tail` attribute of that same `<a>` element. It's for
        # this reason that, depending on whether the element being constructed has
        # non-string a child element, we need to assign a `text` vs `tail` attribute
        # to that element or the last non-string child respectively.
        elif len(element):
            last_child = element[-1]
            last_child.tail = f"{last_child.tail or ''}{c}"
        else:
            element.text = f"{element.text or ''}{c}"


def _generate_vdom_children(
    node: etree._Element, transforms: Iterable[_ModelTransform], intercept_links: bool
) -> list[VdomDict | str]:
    """Generates a list of VDOM children from an lxml node.

    Inserts inner text and/or tail text in between VDOM children, if necessary.
    """
    return (  # Get the inner text of the current node
        [node.text] if node.text else []
    ) + list(
        chain(
            *(
                # Recursively convert each child node to VDOM
                [_etree_to_vdom(child, transforms, intercept_links)]
                # Insert the tail text between each child node
                + ([child.tail] if child.tail else [])
                for child in node.iterchildren(None)
            )
        )
    )


def component_to_vdom(component: Component) -> VdomDict:
    """Convert the first render of a component into a VDOM dictionary"""
    result = component.render()

    if result is None:
        return h.fragment()
    if isinstance(result, dict):
        return result
    if hasattr(result, "render"):
        return component_to_vdom(cast(Component, result))
    return h.div(result) if isinstance(result, str) else h.div()


def _react_attribute_to_html(key: str, value: Any) -> tuple[str, str]:
    """Convert a React attribute to an HTML attribute string."""
    if callable(value):  # nocov
        raise TypeError(f"Cannot convert callable attribute {key}={value} to HTML")

    if key == "style":
        if isinstance(value, dict):
            value = ";".join(
                f"{CAMEL_CASE_PATTERN.sub('-', k).lower()}:{v}"
                for k, v in value.items()
            )

    # Convert special attributes to kebab-case
    elif key in DASHED_HTML_ATTRS:
        key = CAMEL_CASE_PATTERN.sub("-", key)

    # Retain data-* and aria-* attributes as provided
    elif key.startswith("data-") or key.startswith("aria-"):
        return key, str(value)

    return key.lower(), str(value)


# see list of HTML attributes with dashes in them:
# https://developer.mozilla.org/en-US/docs/Web/HTML/Attributes#attribute_list
DASHED_HTML_ATTRS = {"acceptCharset", "httpEquiv"}

# Pattern for delimitting camelCase names (e.g. camelCase to camel-case)
CAMEL_CASE_PATTERN = re.compile(r"(?<!^)(?=[A-Z])")


def import_dotted_path(dotted_path: str) -> Any:
    """Imports a dotted path and returns the callable."""
    if "." not in dotted_path:
        raise ValueError(f'"{dotted_path}" is not a valid dotted path.')

    module_name, component_name = dotted_path.rsplit(".", 1)

    try:
        module = import_module(module_name)
    except ImportError as error:
        msg = f'ReactPy failed to import "{module_name}"'
        raise ImportError(msg) from error

    try:
        return getattr(module, component_name)
    except AttributeError as error:
        msg = f'ReactPy failed to import "{component_name}" from "{module_name}"'
        raise AttributeError(msg) from error


class Singleton:
    """A class that only allows one instance to be created."""

    def __new__(cls, *args, **kw):
        if not hasattr(cls, "_instance"):
            orig = super()
            cls._instance = orig.__new__(cls, *args, **kw)
        return cls._instance


def str_to_bool(s: str) -> bool:
    """Convert a string to a boolean value."""
    return s.lower() in {"y", "yes", "t", "true", "on", "1"}
