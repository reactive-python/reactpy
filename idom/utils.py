from html.parser import HTMLParser as _HTMLParser

from typing import List, Tuple, Any, Dict, Callable, Optional, Generic, TypeVar


_RefValue = TypeVar("_RefValue")


class Ref(Generic[_RefValue]):
    """Hold a reference to a value

    This is used in imperative code to mutate the state of this object in order to
    incur side effects. Generally refs should be avoided if possible, but sometimes
    they are required.

    Attributes:
        current: The present value.

    Notes:
        You can compare the contents for two ``Ref`` objects using the ``==`` operator.
    """

    __slots__ = "current"

    def __init__(self, initial_value: _RefValue) -> None:
        self.current = initial_value

    def set_current(self, new: _RefValue) -> _RefValue:
        """Set the current value and return what is now the old value

        This is nice to use in ``lambda`` functions.
        """
        old = self.current
        self.current = new
        return old

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, Ref) and (other.current == self.current)

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.current})"


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
    def model(self) -> Dict[str, Any]:
        return self._node_stack[0]

    def feed(self, data: str) -> None:
        self._node_stack.append(self._make_vdom("div", {}))
        super().feed(data)

    def reset(self) -> None:
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
