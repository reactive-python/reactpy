from __future__ import annotations

import re
from itertools import chain
from typing import Any, Callable, Generic, Iterable, TypeVar, cast

from lxml import etree
from lxml.html import fromstring, tostring

import idom
from idom.core.types import VdomDict


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

    __slots__ = "current"

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

    def __eq__(self, other: Any) -> bool:
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


def vdom_to_html(vdom: VdomDict) -> str:
    """Convert a VDOM dictionary into an HTML string

    Only the following keys are translated to HTML:

    - ``tagName``
    - ``attributes``
    - ``children`` (must be strings or more VDOM dicts)

    Parameters:
        vdom: The VdomDict element to convert to HTML
    """
    temp_root = etree.Element("__temp__")
    _add_vdom_to_etree(temp_root, vdom)
    html = cast(bytes, tostring(temp_root)).decode()
    # strip out temp root <__temp__> element
    return html[10:-11]


def html_to_vdom(
    html: str, *transforms: _ModelTransform, strict: bool = True
) -> VdomDict:
    """Transform HTML into a DOM model. Unique keys can be provided to HTML elements
    using a ``key=...`` attribute within your HTML tag.

    Parameters:
        html:
            The raw HTML as a string
        transforms:
            Functions of the form ``transform(old) -> new`` where ``old`` is a VDOM
            dictionary which will be replaced by ``new``. For example, you could use a
            transform function to add highlighting to a ``<code/>`` block.
        strict:
            If ``True``, raise an exception if the HTML does not perfectly follow HTML5
            syntax.
    """
    if not isinstance(html, str):  # pragma: no cover
        raise TypeError(f"Expected html to be a string, not {type(html).__name__}")

    # If the user provided a string, convert it to a list of lxml.etree nodes
    try:
        root_node: etree._Element = fromstring(
            html.strip(),
            parser=etree.HTMLParser(
                remove_comments=True,
                remove_pis=True,
                remove_blank_text=True,
                recover=not strict,
            ),
        )
    except etree.XMLSyntaxError as e:
        if not strict:
            raise e  # pragma: no cover
        raise HTMLParseError(
            "An error has occurred while parsing the HTML.\n\n"
            "This HTML may be malformatted, or may not perfectly adhere to HTML5.\n"
            "If you believe the exception above was due to something intentional, "
            "you can disable the strict parameter on html_to_vdom().\n"
            "Otherwise, repair your broken HTML and try again."
        ) from e

    return _etree_to_vdom(root_node, transforms)


class HTMLParseError(etree.LxmlSyntaxError):  # type: ignore[misc]
    """Raised when an HTML document cannot be parsed using strict parsing."""


def _etree_to_vdom(
    node: etree._Element, transforms: Iterable[_ModelTransform]
) -> VdomDict:
    """Transform an lxml etree node into a DOM model

    Parameters:
        node:
            The ``lxml.etree._Element`` node
        transforms:
            Functions of the form ``transform(old) -> new`` where ``old`` is a VDOM
            dictionary which will be replaced by ``new``. For example, you could use a
            transform function to add highlighting to a ``<code/>`` block.
    """
    if not isinstance(node, etree._Element):  # pragma: no cover
        raise TypeError(
            f"Expected node to be a etree._Element, not {type(node).__name__}"
        )

    # Recursively call _etree_to_vdom() on all children
    children = _generate_vdom_children(node, transforms)

    # Convert the lxml node to a VDOM dict
    attributes = dict(node.items())
    key = attributes.pop("key", None)

    vdom: VdomDict
    if hasattr(idom.html, node.tag):
        vdom = getattr(idom.html, node.tag)(attributes, *children, key=key)
    else:
        vdom = {"tagName": node.tag}
        if children:
            vdom["children"] = children
        if attributes:
            vdom["attributes"] = attributes
        if key is not None:
            vdom["key"] = key

    # Perform any necessary mutations on the VDOM attributes to meet VDOM spec
    _mutate_vdom(vdom)

    # Apply any provided transforms.
    for transform in transforms:
        vdom = transform(vdom)

    return vdom


def _add_vdom_to_etree(parent: etree._Element, vdom: VdomDict | dict[str, Any]) -> None:
    try:
        tag = vdom["tagName"]
    except KeyError as e:
        raise TypeError(f"Expected a VDOM dict, not {vdom}") from e
    else:
        vdom = cast(VdomDict, vdom)

    if tag:
        element = etree.SubElement(parent, tag)
        element.attrib.update(
            _vdom_attr_to_html_str(k, v) for k, v in vdom.get("attributes", {}).items()
        )
    else:
        element = parent

    for c in vdom.get("children", []):
        if isinstance(c, dict):
            _add_vdom_to_etree(element, c)
        else:
            """
            LXML handles string children by storing them under `text` and `tail`
            attributes of Element objects. The `text` attribute, if present, effectively
            becomes that element's first child. Then the `tail` attribute, if present,
            becomes a sibling that follows that element. For example, consider the
            following HTML:

                <p><a>hello</a>world</p>

            In this code sample, "hello" is the `text` attribute of the `<a>` element
            and "world" is the `tail` attribute of that same `<a>` element. It's for
            this reason that, depending on whether the element being constructed has
            non-string a child element, we need to assign a `text` vs `tail` attribute
            to that element or the last non-string child respectively.
            """
            if len(element):
                last_child = element[-1]
                last_child.tail = f"{last_child.tail or ''}{c}"
            else:
                element.text = f"{element.text or ''}{c}"


def _mutate_vdom(vdom: VdomDict) -> None:
    """Performs any necessary mutations on the VDOM attributes to meet VDOM spec.

    Currently, this function only transforms the ``style`` attribute into a dictionary whose keys are
    camelCase so as to be renderable by React.

    This function may be extended in the future.
    """
    # Determine if the style attribute needs to be converted to a dict
    if (
        "attributes" in vdom
        and "style" in vdom["attributes"]
        and isinstance(vdom["attributes"]["style"], str)
    ):
        # Convince type checker that it's safe to mutate attributes
        assert isinstance(vdom["attributes"], dict)

        # Convert style attribute from str -> dict with camelCase keys
        vdom["attributes"]["style"] = {
            _hypen_to_camel_case(key.strip()): value.strip()
            for key, value in (
                part.split(":", 1)
                for part in vdom["attributes"]["style"].split(";")
                if ":" in part
            )
        }


def _generate_vdom_children(
    node: etree._Element, transforms: Iterable[_ModelTransform]
) -> list[VdomDict | str]:
    """Generates a list of VDOM children from an lxml node.

    Inserts inner text and/or tail text inbetween VDOM children, if necessary.
    """
    return (  # Get the inner text of the current node
        [node.text] if node.text else []
    ) + list(
        chain(
            *(
                # Recursively convert each child node to VDOM
                [_etree_to_vdom(child, transforms)]
                # Insert the tail text between each child node
                + ([child.tail] if child.tail else [])
                for child in node.iterchildren(None)
            )
        )
    )


def _hypen_to_camel_case(string: str) -> str:
    """Convert a hypenated string to camelCase."""
    first, _, remainder = string.partition("-")
    return first.lower() + remainder.title().replace("-", "")


def del_html_head_body_transform(vdom: VdomDict) -> VdomDict:
    """Transform intended for use with `html_to_vdom`.

    Removes `<html>`, `<head>`, and `<body>` while preserving their children.

    Parameters:
        vdom:
            The VDOM dictionary to transform.
    """
    if vdom["tagName"] in {"html", "body", "head"}:
        return {"tagName": "", "children": vdom["children"]}
    return vdom


def _vdom_attr_to_html_str(key: str, value: Any) -> tuple[str, str]:
    if key == "style":
        if isinstance(value, dict):
            value = ";".join(
                # We lower only to normalize - CSS is case-insensitive:
                # https://www.w3.org/TR/css-fonts-3/#font-family-casing
                f"{_CAMEL_CASE_SUB_PATTERN.sub('-', k).lower()}:{v}"
                for k, v in value.items()
            )
    elif (
        # camel to data-* attributes
        key.startswith("data")
        # camel to aria-* attributes
        or key.startswith("aria")
        # handle special cases
        or key in _DASHED_HTML_ATTRS
    ):
        key = _CAMEL_CASE_SUB_PATTERN.sub("-", key)

    assert not callable(
        value
    ), f"Could not convert callable attribute {key}={value} to HTML"

    # Again, we lower the attribute name only to normalize - HTML is case-insensitive:
    # http://w3c.github.io/html-reference/documents.html#case-insensitivity
    return key.lower(), str(value)


# Pattern for delimitting camelCase names (e.g. camelCase to camel-case)
_CAMEL_CASE_SUB_PATTERN = re.compile(r"(?<!^)(?=[A-Z])")

# see list of HTML attributes with dashes in them:
# https://developer.mozilla.org/en-US/docs/Web/HTML/Attributes#attribute_list
_DASHED_HTML_ATTRS = {"acceptCharset", "httpEquiv"}
