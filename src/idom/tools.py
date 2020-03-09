from html.parser import HTMLParser as _HTMLParser

from typing import List, Tuple, Any, Dict, TypeVar, Generic, Callable, Optional


_R = TypeVar("_R", bound=Any)  # Var reference


class Var(Generic[_R]):
    """A variable for holding a reference to an object.

    Variables are useful when multiple elements need to share data. This is usually
    discouraged, but can be useful in certain situations. For example, you might use
    a reference to keep track of a user's selection from a list of options:

    .. code-block:: python

        def option_picker(handler, option_names):
            selection = Var()
            options = [option(n, selection) for n in option_names]
            return idom.vdom("div", options, picker(handler, selection))

        def option(name, selection):
            events = idom.Events()

            @events.on("click")
            def select():
                # set the current selection to the option name
                selection.set(name)

            return idom.vdom("button", eventHandlers=events)

        def picker(handler, selection):
            events = idom.Events()

            @events.on("click")
            def handle():
                # passes the current option name to the handler
                handler(selection.get())

            return idom.vdom("button", "Use" eventHandlers=events)
    """

    __slots__ = ("_current",)

    def __init__(self, value: _R) -> None:
        self._current = value

    def set(self, new: _R) -> _R:
        old = self._current
        self._current = new
        return old

    def get(self) -> _R:
        return self._current

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Var):
            return bool(self.get() == other.get())
        else:
            return False

    def __repr__(self) -> str:
        return "Var(%r)" % self.get()


_ModelTransform = Callable[[Dict[str, Any]], Any]


def html_to_vdom(source: str, *transforms: _ModelTransform) -> Dict[str, Any]:
    """Transform HTML into a DOM model

    Parameters:
        source:
            The raw HTML as a string
        transforms:
            Functions of the form ``transform(old) -> new`` where ``old`` is a VDOM
            dictionary which will be replaced by ``new``. You might use a transform
            function to add highlighting to a ``<code/>`` block.
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
