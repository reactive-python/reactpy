from html.parser import HTMLParser as _HTMLParser

from typing import List, Tuple, Any, Dict, Union, Optional, TypeVar, Generic, Callable


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
            return idom.node("div", options, picker(handler, selection))

        def option(name, selection):
            events = idom.Events()

            @events.on("click")
            def select():
                # set the current selection to the option name
                selection.set(name)

            return idom.node("button", eventHandlers=events)

        def picker(handler, selection):
            events = idom.Events()

            @events.on("click")
            def handle():
                # passes the current option name to the handler
                handler(selection.get())

            return idom.node("button", "Use" eventHandlers=events)
    """

    __slots__ = ("__current",)

    def __init__(self, value: _R) -> None:
        self.__current = value

    def set(self, new: _R) -> _R:
        old = self.__current
        self.__current = new
        return old

    def get(self) -> _R:
        return self.__current

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Var):
            return bool(self.get() == other.get())
        else:
            return False

    def __repr__(self) -> str:
        return "Var(%r)" % self.get()


_ModelOrStr = Union[Dict[str, Any], str]
_ModelTransform = Callable[[_ModelOrStr], None]


def html_to_vdom(
    source: str, transform: Optional[_ModelTransform] = None
) -> Dict[str, Any]:
    """Transform HTML into a DOM model

    Parameters:
        source:
            The raw HTML as a string
        transform:
            A function for transforming each model as it is created. For example,
            you might use a transform function to add highlighting to a ``<code/>``
            block.
    """
    parser = HtmlParser(transform)
    parser.feed(source)
    return parser.model()


class HtmlParser(_HTMLParser):
    def __init__(self, transform: Optional[_ModelTransform] = None):
        super().__init__()
        if transform is not None:
            self._transform = transform

    def model(self) -> Dict[str, Any]:
        root: Dict[str, Any] = self._node_stack[0]
        first_child: Dict[str, Any] = root["children"][0]
        return first_child

    def feed(self, data: str) -> None:
        self._node_stack.append(self._make_node("div", {}))
        super().feed(data)

    def reset(self) -> None:
        self._node_stack: List[Dict[str, Any]] = []
        super().reset()

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, str]]) -> None:
        new = self._make_node(tag, dict(attrs))
        current = self._node_stack[-1]
        current["children"].append(new)
        self._node_stack.append(new)

    def handle_endtag(self, tag: str) -> None:
        node = self._node_stack.pop(-1)
        self._transform(node)
        if not node["attributes"]:
            del node["attributes"]
        if not node["children"]:
            del node["children"]

    def handle_data(self, data: str) -> None:
        self._node_stack[-1]["children"].append(data)

    @staticmethod
    def _make_node(tag: str, attrs: Dict[str, Any]) -> Dict[str, Any]:
        if "style" in attrs:
            style = attrs["style"]
            if isinstance(style, str):
                style_dict = {}
                for k, v in (part.split(":", 1) for part in style.split(";")):
                    title_case_key = k.title().replace("-", "")
                    camel_case_key = title_case_key[:1].lower() + title_case_key[1:]
                    style_dict[camel_case_key] = v
                attrs["style"] = style_dict
        return {"tagName": tag, "attributes": attrs, "children": []}

    @staticmethod
    def _transform(node: Dict[str, Any]) -> None:
        ...
