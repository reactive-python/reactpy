from html.parser import HTMLParser as _HTMLParser
from typing import Any, Callable, Dict, Generic, List, Optional, Tuple, TypeVar


_RefValue = TypeVar("_RefValue")
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


_ModelTransform = Callable[[Dict[str, Any]], Any]


def html_to_vdom(source: str, *transforms: _ModelTransform) -> Dict[str, Any]:
    """Transform HTML into a DOM model

    Parameters:
        source:
            The raw HTML as a string
        transforms:
            Functions of the form ``transform(old) -> new`` where ``old`` is a VDOM
            dictionary which will be replaced by ``new``. For example, you could use a
            transform function to add highlighting to a ``<code/>`` block.
    """
    parser = HtmlParser()
    parser.feed(source)
    root = parser.model()
    to_visit = [root]
    while to_visit:
        node = to_visit.pop(0)
        if isinstance(node, dict) and "children" in node:
            transformed = []
            for child in node["children"]:
                if isinstance(child, dict):
                    for t in transforms:
                        child = t(child)
                if child is not None:
                    transformed.append(child)
                    to_visit.append(child)
            node["children"] = transformed
            if "attributes" in node and not node["attributes"]:
                del node["attributes"]
            if "children" in node and not node["children"]:
                del node["children"]
    return root


class HtmlParser(_HTMLParser):
    """HTML to VDOM parser

    Example:

        .. code-block::

            parser = HtmlParser()

            parser.feed(an_html_string)
            parser.feed(another_html_string)
            ...

            vdom = parser.model()
    """

    def model(self) -> Dict[str, Any]:
        """Get the current state of parsed VDOM model"""
        return self._node_stack[0]

    def feed(self, data: str) -> None:
        """Feed in HTML that will update the :meth:`HtmlParser.model`"""
        self._node_stack.append(self._make_vdom("div", {}))
        super().feed(data)

    def reset(self) -> None:
        """Reset the state of the parser"""
        self._node_stack: List[Dict[str, Any]] = []
        super().reset()

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        new = self._make_vdom(tag, dict(attrs))
        current = self._node_stack[-1]
        current["children"].append(new)
        self._node_stack.append(new)

    def handle_endtag(self, tag: str) -> None:
        del self._node_stack[-1]

    def handle_data(self, data: str) -> None:
        self._node_stack[-1]["children"].append(data)

    @staticmethod
    def _make_vdom(tag: str, attrs: Dict[str, Any]) -> Dict[str, Any]:
        if "style" in attrs:
            style = attrs["style"]
            if isinstance(style, str):
                style_dict = {}
                for k, v in (part.split(":", 1) for part in style.split(";") if part):
                    title_case_key = k.title().replace("-", "")
                    camel_case_key = title_case_key[:1].lower() + title_case_key[1:]
                    style_dict[camel_case_key] = v
                attrs["style"] = style_dict
        return {"tagName": tag, "attributes": attrs, "children": []}
