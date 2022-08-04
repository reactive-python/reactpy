from itertools import chain
from typing import Any, Callable, Dict, Generic, List, TypeVar, Union

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


def html_to_vdom(html: str, *transforms: _ModelTransform):
    """Transform HTML into a DOM model
    Parameters:
        source:
            The raw HTML as a string
        transforms:
            Functions of the form ``transform(old) -> new`` where ``old`` is a VDOM
            dictionary which will be replaced by ``new``. For example, you could use a
            transform function to add highlighting to a ``<code/>`` block.
    """

    if not isinstance(html, str):
        raise TypeError("html_to_vdom expects a string!")

    return _HtmlToVdom().convert(html, *transforms)


class _HtmlToVdom:
    def convert(self, html: Union[str, etree._Element], *transforms: _ModelTransform):
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
            raise TypeError(
                f"HtmlToVdom encountered unsupported type {type(html)} from {html}"
            )

        # Convert the lxml node to a VDOM dict.
        vdom = {"tagName": node.tag}
        self._set_key_value(vdom, "children", self._generate_child_vdom(node))
        self._set_key_value(vdom, "attributes", dict(node.items()))
        self._vdom_mutations(vdom)

        # Apply any provided transforms.
        for transform in transforms:
            vdom = transform(vdom)

        # The root node is always a React Fragment
        if root_node:
            vdom["tagName"] = ""

        return vdom

    @staticmethod
    def _set_key_value(vdom: Dict, key: str, value: Union[Dict, List]):
        """Sets a key/value on a dictionary only if the iterable value's length is greater than 0."""
        if len(value):
            vdom[key] = value

    @staticmethod
    def _vdom_mutations(vdom: Dict):
        """Performs any necessary mutations on the VDOM attributes to meet VDOM spec
        and/or to make elements properly renderable in React."""
        # Convert style attributes to VDOM spec
        if "attributes" in vdom and "style" in vdom["attributes"]:
            style = vdom["attributes"]["style"]
            if isinstance(style, str):
                style_dict = {}
                for k, v in (part.split(":", 1) for part in style.split(";") if part):
                    title_case_key = k.title().replace("-", "")
                    camel_case_key = title_case_key[:1].lower() + title_case_key[1:]
                    style_dict[camel_case_key] = v
                vdom["attributes"]["style"] = style_dict

        # Set key attribute for scripts to prevent re-execution during re-renders
        if vdom["tagName"] == "script":
            if not isinstance(vdom["children"][0], str):
                # The script's source should always be the first child
                raise LookupError("Could not find script's contents!")
            if vdom["children"][0]:
                vdom["key"] = vdom["children"][0]

    def _generate_child_vdom(self, node: etree._Element) -> list:
        """Recursively generate a list of VDOM children from an lxml node."""
        children = [node.text] + list(
            chain(*([self.convert(child), child.tail] for child in node.iterchildren(None)))
        )

        # Remove None from the list of children from empty text/tail values
        return list(filter(None, children))
