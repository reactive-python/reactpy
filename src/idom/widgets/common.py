from typing import Any, Callable, Tuple, Optional

from idom.core.element import ElementConstructor, Element, element
from idom.core.vdom import VdomDict, ImportSourceDict, vdom
from idom.tools import Var


class Import:
    """Import a react library

    Once imported, you can instantiate the library's components by calling them
    via attribute-access. For example, Ant Design provides a date-picker interface
    and an ``onChange`` callback which could be leveraged in the following way:

    .. code-block:: python

        antd = idom.Import("https://dev.jspm.io/antd")
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

    def __init__(self, package: str, fallback: Optional[str] = None) -> None:
        self._package = package
        self._fallback = fallback

    def __getattr__(self, tag: str) -> Callable[..., VdomDict]:
        """Attribute is a constructor for a VDOM dict with that tagName."""

        def constructor(*args: Any, **kwargs: Any) -> VdomDict:
            return self(tag, *args, **kwargs)

        return constructor

    def __call__(self, *args: Any, **kwargs: Any) -> VdomDict:
        import_source = ImportSourceDict(source=self._package, fallback=self._fallback)
        return vdom(import_source=import_source, *args, **kwargs)

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self._package!r})"


def hotswap(
    shared: bool = False,
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
