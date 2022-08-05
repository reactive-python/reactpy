from itertools import chain
from typing import Any, Callable, Dict, Generic, Iterable, List, TypeVar, Union

from lxml import etree
from lxml.html import fragment_fromstring


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


def html_to_vdom(html: Union[str, etree._Element], *transforms: _ModelTransform):
    """Transform HTML into a DOM model
    Parameters:
        source:
            The raw HTML as a string
        transforms:
            Functions of the form ``transform(old) -> new`` where ``old`` is a VDOM
            dictionary which will be replaced by ``new``. For example, you could use a
            transform function to add highlighting to a ``<code/>`` block.
    """

    # If the user provided a string, convert it to an lxml.etree node.
    if isinstance(html, str):
        parser = etree.HTMLParser()
        node = fragment_fromstring(html, create_parent=True, parser=parser)
        root_node = True  # Only the root node is a HTML string
    elif isinstance(html, etree._Element):
        node = html
        root_node = False
    else:
        raise TypeError(
            f"HtmlToVdom encountered unsupported type {type(html)} from {html}"
        )

    # Convert the lxml node to a VDOM dict.
    vdom = {
        "tagName": node.tag,
        "children": _generate_vdom_children(node, transforms),
        "attributes": dict(node.items()),
        "eventHandlers": {},
        "importSource": {},
        "key": "",
        "error": "",
    }
    _mutate_vdom(vdom)

    # Apply any provided transforms.
    for transform in transforms:
        vdom = transform(vdom)

    # The root node is rendered as a React Fragment
    if root_node:
        vdom["tagName"] = ""

    # Get rid of empty VDOM fields
    _prune_vdom_fields(vdom)

    return vdom


def _mutate_vdom(vdom: Dict):
    """Performs any necessary mutations on the VDOM attributes to meet VDOM spec
    and/or to make elements properly renderable in React."""
    # Convert style attributes to VDOM spec
    if "style" in vdom["attributes"] and isinstance(vdom["attributes"]["style"], str):
        vdom["attributes"]["style"] = {
            _hypen_to_camel_case(key.strip()): value.strip()
            for key, value in (
                part.split(":", 1)
                for part in vdom["attributes"]["style"].split(";")
                if ":" in part
            )
        }

    # Set key attribute for scripts to prevent re-execution during re-renders
    if vdom["tagName"] == "script":
        if not isinstance(vdom["children"][0], str):
            # The script's source should always be the first child
            raise LookupError("Could not find script's contents!")
        if vdom["children"][0]:
            vdom["key"] = vdom["children"][0]


def _prune_vdom_fields(vdom: Dict):
    """Remove unneeded fields from VDOM dict."""
    if not len(vdom["children"]):
        del vdom["children"]
    if not len(vdom["attributes"]):
        del vdom["attributes"]
    if not len(vdom["eventHandlers"]):
        del vdom["eventHandlers"]
    if not len(vdom["importSource"]):
        del vdom["importSource"]
    if not vdom["key"]:
        del vdom["key"]
    if not vdom["error"]:
        del vdom["error"]


def _generate_vdom_children(
    node: etree._Element, transforms: Iterable[_ModelTransform]
) -> List[Union[Dict, str]]:
    """Recursively generate a list of VDOM children from an lxml node.
    Inserts inner text and/or tail text inbetween VDOM children, if necessary."""
    return ([node.text] if node.text else []) + list(
        chain(
            *(
                [html_to_vdom(child, *transforms)]
                + ([child.tail] if child.tail else [])
                for child in node.iterchildren(None)
            )
        )
    )


def _hypen_to_camel_case(css_key: str) -> str:
    """Convert a hypenated string to camelCase."""
    first_word, *subsequent_words = css_key.split("-")

    # Use map() to titlecase all subsequent words
    return "".join([first_word.lower(), *map(str.title, subsequent_words)])
