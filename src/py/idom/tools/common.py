from base64 import b64encode
from io import BytesIO

from typing import Any, Callable, Dict, TypeVar, Generic, List, Tuple, Optional, Union

from idom.core import AbstractElement, ElementConstructor, Element, element
from .bunch import Bunch


def node(tag: str, *children: Any, **attributes: Any) -> Bunch:
    """A helper function for generating :term:`VDOM` dictionaries."""
    merged_children: List[Any] = []

    for c in children:
        if isinstance(c, (list, tuple)):
            merged_children.extend(c)
        else:
            merged_children.append(c)

    model = Bunch(tagName=tag)

    if merged_children:
        model.children = merged_children
    if "eventHandlers" in attributes:
        model.eventHandlers = attributes.pop("eventHandlers")
    if attributes:
        model.attributes = attributes

    return model


def node_constructor(tag: str, allow_children: bool = True) -> Callable[..., Bunch]:
    """Create a constructor for nodes with the given tag name."""

    def constructor(*children: Any, **attributes: Any) -> Bunch:
        if not allow_children and children:
            raise TypeError(f"{tag!r} nodes cannot have children.")
        return node(tag, *children, **attributes)

    constructor.__name__ = tag
    qualname_prefix = constructor.__qualname__.rsplit(".", 1)[0]
    constructor.__qualname__ = qualname_prefix + f".{tag}"
    constructor.__doc__ = f"""Create a new ``<{tag}/>`` - returns :term:`VDOM`."""
    return constructor


def hotswap(
    shared: bool = False
) -> Tuple[Callable[[ElementConstructor], None], ElementConstructor]:
    current_root: Var[Optional[Element]] = Var(None)
    current_swap: Var[Callable[[], Any]] = Var(lambda: {"tagName": "div"})

    @element
    async def HotSwap(self: Element) -> Any:
        if shared:
            current_root.set(self)
        make_element = current_swap.get()
        return make_element()

    def swap(element: ElementConstructor, *args: Any, **kwargs: Any) -> None:
        current_swap.set(lambda: element(*args, **kwargs))
        if shared:
            hot = current_root.get()
            if hot is not None:
                hot.update()

    return swap, HotSwap


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


class Image(AbstractElement):

    __slots__ = ("_source", "_format", "_buffer")

    def __init__(self, format: str, value: str = ""):
        super().__init__()
        if format == "svg":
            format = "svg+xml"
        self._buffer = BytesBuffer(value.encode(), self._set_source)
        self._source = b""
        self._format = format

    @property
    def io(self) -> "BytesBuffer":
        return self._buffer

    async def render(self) -> Dict[str, Any]:
        self._buffer.close()
        source = b64encode(self._source).decode()
        return {
            "tagName": "img",
            "attributes": {"src": f"data:image/{self._format};base64,{source}"},
        }

    def _set_source(self, value: bytes) -> None:
        self._source = value


class BytesBuffer(BytesIO):
    def __init__(
        self, value: Union[bytes, str], close_callback: Callable[[bytes], None]
    ) -> None:
        self._on_close_callback = close_callback
        if isinstance(value, str):
            super().__init__(value.encode())
        else:
            super().__init__(value)

    def write(self, value: Union[bytes, str]) -> int:
        if isinstance(value, str):
            return super().write(value.encode())
        else:
            return super().write(value)

    def close(self) -> None:
        if not self.closed:
            self._on_close_callback(self.getvalue())
        super().close()
