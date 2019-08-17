from typing import Any, Callable, Dict, List, Tuple, Optional

import idom
from idom.core.element import ElementConstructor, AbstractElement, Element, element


def node(tag: Optional[str], *children: Any, **attributes: Any) -> Dict[str, Any]:
    """A helper function for generating DOM model dictionaries."""
    merged_children: List[Any] = []

    for c in children:
        if isinstance(c, (list, tuple)):
            merged_children.extend(c)
        else:
            merged_children.append(c)

    model: Dict[str, Any] = {"tagName": tag}

    if merged_children:
        model["children"] = merged_children

    for top_level_attr in ["eventHandlers", "importSource"]:
        if top_level_attr in attributes:
            model[top_level_attr] = attributes.pop(top_level_attr)

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


class Module:
    def __init__(self, code: str) -> None:
        super().__init__()
        self._code = code

    def __getattr__(self, tag: str) -> Callable[..., "ModuleElement"]:
        def constructor(
            *children: Any, fallback: Optional[str] = None, **attributes: Any
        ) -> "ModuleElement":
            return self(tag, *children, fallback=fallback, **attributes)

        return constructor

    def __call__(
        self,
        tag: Optional[str] = None,
        *children: Any,
        fallback: Optional[str] = None,
        **attributes: Any,
    ) -> "ModuleElement":
        return ModuleElement(self._code, tag, children, attributes, fallback)


class ModuleElement(AbstractElement):
    def __init__(
        self,
        code: str,
        tag: Optional[str],
        children: Tuple[Any, ...],
        attributes: Dict[str, Any],
        fallback: Optional[str],
    ) -> None:
        super().__init__()
        self._code = code
        self._tag = tag
        self._children = children
        self._attributes = attributes
        self._fallback = fallback

    async def render(self) -> Any:
        return {
            "tagName": self._tag,
            "children": self._children,
            "attributes": self._attributes,
            "importSource": {
                "id": hex(hash(self._code)),
                "source": self._code,
                "fallback": None,
            },
        }


class Import:
    """Import a react library

    Once imported, you can instantiate the library's components by calling them
    via attribute-access. For example, Ant Design provides a date-picker interface
    and an ``onChange`` callback which could be leveraged in the following way:

    .. code-block:: python

        antd = idom.Package("https://dev.jspm.io/antd")
        # you'll often need to link to the css stylesheet for the library.
        css = idom.html.link(rel="stylesheet", type="text/css", href="https://dev.jspm.io/antd/dist/antd.css")

        @idom.element
        async def AntDatePicker(self):

            async def changed(moment, datestring):
                print("CLIENT DATETIME:", moment)
                print("PICKED DATETIME:", datestring)

            picker = antd.DatePicker(onChange=changed, fallback="Loading...")
            return idom.html.div(picker, css)
    """

    def __init__(self, pkg: str) -> None:
        self._pkg = pkg

    def __getattr__(self, tag: str) -> Callable[..., "ImportElement"]:
        def constructor(
            *children: Any, fallback: Optional[str] = None, **attributes: Any
        ) -> "ImportElement":
            return self(tag, *children, fallback=fallback, **attributes)

        return constructor

    def __call__(
        self,
        tag: Optional[str] = None,
        *children: Any,
        fallback: Optional[str] = None,
        **attributes: Any,
    ) -> "ImportElement":
        return ImportElement(self._pkg, tag, children, attributes, fallback)


class ImportElement(AbstractElement):
    """A component from a React library.

    You should probably use :class:`Package` to instantiate this element.
    """

    __slots__ = ("_package", "_tag", "_children", "_attributes", "_fallback")

    def __init__(
        self,
        package: str,
        tag: Optional[str],
        children: Tuple[Any, ...],
        attributes: Dict[str, Any],
        fallback: Optional[str],
    ) -> None:
        super().__init__()
        self._package = package
        self._tag = tag
        self._children = children
        self._attributes = attributes
        self._fallback = fallback

    async def render(self) -> Any:
        source = {
            "id": hex(hash(self._package)),
            "source": f"import('{self._package}').then(pkg => pkg.default);",
            "fallback": self._fallback,
        }
        return node(self._tag, importSource=source, *self._children, **self._attributes)


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
    current_root: idom.Var[Optional[Element]] = idom.Var(None)
    current_swap: idom.Var[Callable[[], Any]] = idom.Var(lambda: {"tagName": "div"})
    last_element: idom.Var[Optional[Element]] = idom.Var(None)

    @element
    async def HotSwap(self: Element) -> Any:
        if shared:
            current_root.set(self)
        make_element = current_swap.get()
        new = make_element()
        old = last_element.set(new)
        if isinstance(old, Element):
            # because the hotswap is done via side-effects there's no way for
            # the layout to know to unmount the old element so we do it manually
            await old.unmount()
        return new

    def swap(element: ElementConstructor, *args: Any, **kwargs: Any) -> None:
        current_swap.set(lambda: element(*args, **kwargs))

        if shared:
            hot = current_root.get()
            if hot is not None:
                hot.update()

    return swap, HotSwap
