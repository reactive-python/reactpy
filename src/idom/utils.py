from itertools import chain
from typing import Any, Callable, Dict, Generic, Iterable, List, TypeVar, Union

from lxml import etree
from lxml.html import fragments_fromstring

import idom
from idom.core.vdom import VdomDict


_RefValue = TypeVar("_RefValue")
_ModelTransform = Callable[[Dict[str, Any]], Any]
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


def html_to_vdom(html: str, *transforms: _ModelTransform) -> VdomDict:
    """Transform HTML into a DOM model. Unique keys can be provided to HTML elements
    using a ``key=...`` attribute within your HTML tag.

    Parameters:
        source:
            The raw HTML as a string
        transforms:
            Functions of the form ``transform(old) -> new`` where ``old`` is a VDOM
            dictionary which will be replaced by ``new``. For example, you could use a
            transform function to add highlighting to a ``<code/>`` block.
    """
    if not isinstance(html, str):  # pragma: no cover
        raise TypeError(f"Encountered unsupported type {type(html)} from {html}")

    # If the user provided a string, convert it to a list of lxml.etree nodes
    parser = etree.HTMLParser(
        remove_comments=True,
        remove_pis=True,
        remove_blank_text=True,
        recover=False,
    )
    nodes: List = fragments_fromstring(html, no_leading_text=True, parser=parser)
    has_root_node = len(nodes) == 1

    # Find or create a root node
    if has_root_node:
        root_node = nodes[0]
    else:
        # etree.Element requires a non-empty tag - we correct this below
        root_node = etree.Element("TEMP", None, None)
        for child in nodes:
            root_node.append(child)

    # Convert the lxml node to a VDOM dict
    vdom = _etree_to_vdom(root_node, transforms)

    # Change the artificially created root node to a React Fragment, instead of a div
    if not has_root_node:
        vdom["tagName"] = ""

    return vdom


def _etree_to_vdom(
    node: etree._Element, transforms: Iterable[_ModelTransform]
) -> VdomDict:
    """Recusively transform an lxml etree node into a DOM model

    Parameters:
        source:
            The ``lxml.etree._Element`` node
        transforms:
            Functions of the form ``transform(old) -> new`` where ``old`` is a VDOM
            dictionary which will be replaced by ``new``. For example, you could use a
            transform function to add highlighting to a ``<code/>`` block.
    """
    if not isinstance(node, etree._Element):  # pragma: no cover
        raise TypeError(f"Encountered unsupported type {type(node)} from {node}")

    # This will recursively call _etree_to_vdom() on all children
    children = _generate_vdom_children(node, transforms)

    # Convert the lxml node to a VDOM dict
    attributes = dict(node.items())
    key = attributes.pop("key", None)

    if hasattr(idom.html, node.tag):
        vdom = getattr(idom.html, node.tag)(attributes, *children, key=key)
    else:
        vdom: VdomDict = {"tagName": node.tag}
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


def _mutate_vdom(vdom: VdomDict):
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
) -> List[Union[VdomDict, str]]:
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


def _hypen_to_camel_case(css_key: str) -> str:
    """Convert a hypenated string to camelCase."""
    first_word, *subsequent_words = css_key.split("-")

    return "".join(
        [
            # Lowercase the first word
            first_word.lower(),
            # Use map() to titlecase all subsequent words
            *map(str.title, subsequent_words),
        ]
    )
