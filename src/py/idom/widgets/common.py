from typing import Any, Callable, Tuple, Optional

from idom.core.element import ElementConstructor, AbstractElement, Element, element
from idom.core.vdom import VdomDict, vdom
from idom.tools import Var


class Eval:
    """An interface for creating React Components that you can use in your layouts."""

    def __init__(self, code: str, fallback: Optional[str] = None) -> None:
        super().__init__()
        self._code = code
        self._fallback = fallback

    def __getattr__(self, tag: str) -> Callable[..., "EvalElement"]:
        def constructor(*args: Any, **kwargs: Any) -> "EvalElement":
            return self(tag, *args, **kwargs)

        return constructor

    def __call__(self, *args: Any, **kwargs: Any) -> "EvalElement":
        return EvalElement(self._code, self._fallback, vdom(*args, **kwargs))


class EvalElement(AbstractElement):
    """An element created by :class:`Eval` which refers to a React component."""

    def __init__(self, code: str, fallback: Optional[str], model: VdomDict) -> None:
        super().__init__()
        if "importSource" in model:
            raise ValueError("Model already has an import source")
        model["importSource"] = {"source": code, "fallback": fallback}
        self._model = model

    async def render(self) -> VdomDict:
        return self._model


class Import(Eval):
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

    def __init__(self, pkg: str, fallback: Optional[str] = None) -> None:
        if pkg.startswith("/"):
            url = pkg
        else:
            url = f"https://dev.jspm.io/{pkg}"
        code = f"import('{url}').then(pkg => pkg.default);"
        super().__init__(code, fallback)


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
