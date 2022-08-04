from typing import Any, Callable, Dict, Generic, TypeVar, Union

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


def _set_if_val_exists(object, key, value):
    """Sets a key on a dictionary if the value's length is greater than 0."""
    if len(value):
        object[key] = value


def _vdom_attributes(object):
    if "attributes" in object and "style" in object["attributes"]:
        style = object["attributes"]["style"]
        if isinstance(style, str):
            style_dict = {}
            for k, v in (part.split(":", 1) for part in style.split(";") if part):
                title_case_key = k.title().replace("-", "")
                camel_case_key = title_case_key[:1].lower() + title_case_key[1:]
                style_dict[camel_case_key] = v
            object["attributes"]["style"] = style_dict


def _vdom_key(object):
    if object["tagName"] == "script":
        if not isinstance(object["children"][0], str):
            # The script tag contents should be the first child
            raise TypeError("Could not find script tag contents!")
        if object["children"][0]:
            object["key"] = object["children"][0]


def html_to_vdom(html: Union[str, etree._Element], *transforms: _ModelTransform):
    """Convert an lxml.etree node tree into a VDOM dict."""
    # Keep track of whether this is the root node
    root_node = False

    # If the user provided a string, convert it to an lxml.etree node.
    if isinstance(html, str):
        parser = etree.HTMLParser()
        node = fragment_fromstring(html, create_parent=True, parser=parser)
        root_node = True
    elif isinstance(html, etree._Element):
        node = html
    else:
        raise TypeError("html_to_vdom expects a string or lxml.etree._Element")

    # Convert the lxml.etree node to a VDOM dict.
    vdom = {"tagName": node.tag}
    node_children = [node.text] if node.text else []
    node_children.extend([html_to_vdom(child) for child in node.iterchildren(None)])
    _set_if_val_exists(vdom, "children", node_children)
    _set_if_val_exists(vdom, "attributes", dict(node.items()))
    _vdom_attributes(vdom)
    _vdom_key(vdom)

    # Apply any provided transforms.
    for transform in transforms:
        vdom = transform(vdom)

    # The root node is always a React Fragment
    if root_node:
        vdom["tagName"] = ""

    return vdom
