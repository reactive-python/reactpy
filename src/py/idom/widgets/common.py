from base64 import b64encode
from io import BytesIO

from typing import Any, Callable, Dict, TypeVar, Generic, List, Tuple, Optional, Union

from idom.core import AbstractElement, ElementConstructor, Element, element


def node(tag: str, *children: Any, **attributes: Any) -> Dict[str, Any]:
    """A helper function for generating :term:`VDOM` dictionaries."""
    merged_children: List[Any] = []

    for c in children:
        if isinstance(c, (list, tuple)):
            merged_children.extend(c)
        else:
            merged_children.append(c)

    model: Dict[str, Any] = {"tagName": tag}

    if merged_children:
        model["children"] = merged_children
    if "eventHandlers" in attributes:
        model["eventHandlers"] = attributes.pop("eventHandlers")
    if attributes:
        model["attributes"] = attributes
        if "cls" in attributes:
            # you can't use 'class' as a keyword
            model["attributes"]["class"] = attributes.pop("cls")

    return model


def node_constructor(
    tag: str, allow_children: bool = True
) -> Callable[..., Dict[str, Any]]:
    """Create a constructor for nodes with the given tag name."""

    def constructor(*children: Any, **attributes: Any) -> Dict[str, Any]:
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
    """Swap out elements from a layout on the fly.

    Normally you can't change the element functions used to create a layout
    in an imperative manner. However ``hotswap`` allows you to do this so
    long as you set things up ahead of time.

    Parameters:
        shared: Whether or not all views of the layout should be udpated on a swap.

    Example:
        .. code-block:: python

            show, element = idom.hotswap()
            PerClientState(element).daemon("localhost", 8765)

            @element
            def DivOne(self):
                return {"tagName": "div", "children": [1]}

            show(DivOne)

            # displaying the output now will show DivOne

            @element
            def DivTwo(self):
                return {"tagName": "div", "children": [2]}

            show(DivTwo)

            # displaying the output now will show DivTwo
    """
    current_root: Var[Optional[Element]] = Var(None)
    current_swap: Var[Callable[[], Any]] = Var(lambda: {"tagName": "div"})
    last_element: Var[Optional[Element]] = Var(None)

    @element
    async def HotSwap(self: Element) -> Any:
        if shared:
            current_root.set(self)
        make_element = current_swap.get()
        element = make_element()
        last_element.set(element)
        return element

    def swap(element: ElementConstructor, *args: Any, **kwargs: Any) -> None:
        last = last_element.get()
        if last is not None:
            # because the hotswap is done via side-effects there's no way for
            # the layout to know to unmount the old element so we do it manually
            last.unmount()

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
    """An image element.

    Parameters:
        format: The format of the image source (e.g. png or svg)
        value: The image source. If not given use :attr:`Image.io` instead.
        attributes: Attributes assigned to the ``<image/>`` element.
    """

    __slots__ = ("_source", "_format", "_buffer", "_attributes")

    def __init__(self, format: str, value: str = "", **attributes: Any) -> None:
        super().__init__()
        if format == "svg":
            format = "svg+xml"
        self._buffer = BytesBuffer(value.encode(), self._set_source)
        self._source = b""
        self._format = format
        self._attributes = attributes

    @property
    def io(self) -> "BytesBuffer":
        """A file-like interface for loading image source."""
        return self._buffer

    async def render(self) -> Dict[str, Any]:
        self._buffer.close()
        source = b64encode(self._source).decode()
        attrs = self._attributes.copy()
        attrs["src"] = f"data:image/{self._format};base64,{source}"
        return {"tagName": "img", "attributes": attrs}

    def _set_source(self, value: bytes) -> None:
        self._source = value


class BytesBuffer(BytesIO):
    """Similar to :class:`BytesIO` but converts unicode to bytes automatically.

    Parameters:
        value: Initial value for the buffer.
        close_callback: Called with the value of the buffer when it is closed.
    """

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
