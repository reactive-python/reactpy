import inspect
from typing import Any, Callable, Tuple, Optional, Union, Dict

from idom import client
from idom.core.element import ElementConstructor, Element, element
from idom.core.vdom import VdomDict, ImportSourceDict, vdom
from idom.tools import Var


def define_module(name: str, source: Any, raw: bool = False) -> "Import":
    """Add a module to the client

    Parameters:
        name:
            What the module will be named (excluding the ``.js`` file extension). This
            matters if you want to import this module from another later since this will
            be the filename the module is saved under.
        source:
            The module's source.
        raw:
            If false, then ``source`` should be a file path to the module's source.
            If true, this should be the literal source code for the module.

    Returns:
        An :class:`Import` element for the newly defined module.
    """
    if not raw:
        with open(str(source), "r") as f:
            source = f.read()
    else:
        source = inspect.cleandoc(source)
    return Import(client.define_module(name, source))


class Import:
    """Import a react library

    Once imported, you can instantiate the library's components by calling them
    via attribute-access. For example, Ant Design provides a date-picker interface
    and an ``onChange`` callback which could be leveraged in the following way:

    .. code-block:: python

        antd = idom.Import("antd")
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

    def __init__(
        self,
        package: str,
        fallback: Optional[str] = None,
        install: Union[str, bool] = False,
    ) -> None:
        if install:
            if not client.module_exists(package):
                if isinstance(install, str):
                    client.install({install: package})
                else:
                    client.install({package: package})
            new_import_path = client.import_path(package)
            if new_import_path is None:
                raise ValueError(f"Unexpectedly failed to find install of {package}")
            package = new_import_path
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

    Since you can't change the element functions used to create a layout
    in an imperative manner, you can use ``hotswap`` to do this so
    long as you set things up ahead of time.

    Parameters:
        shared: Whether or not all views of the layout should be udpated on a swap.

    Example:
        .. code-block:: python

            import idom

            show, root = idom.hotswap()
            PerClientState(root).daemon("localhost", 8765)

            @idom.element
            def DivOne(self):
                return {"tagName": "div", "children": [1]}

            show(DivOne)

            # displaying the output now will show DivOne

            @idom.element
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

    def swap(constructor: ElementConstructor, *args: Any, **kwargs: Any) -> None:
        current_swap.set(lambda: constructor(*args, **kwargs))
        if shared:
            hot = current_root.get()
            if hot is not None:
                hot.update()

    return swap, HotSwap


def multiview():
    """Dynamically add elements to a layout on the fly

    Since you can't change the element functions used to create a layout
    in an imperative manner, you can use ``multiview`` to do this so
    long as you set things up ahead of time.

    Returns:
        A function for adding views and the root of the dynamic view

    Examples:

        .. code-block::

            import idom

            define, root = idom.widgets.multiview()

            @element
            def Hello(self, phrase):
                return idom.html.h1(["hello " + phrase])

            add_hello = define(Hello)
            hello_world_view_id = add_hello("world")

        Displaying ``root`` with the parameter ``view_id=hello_world_view_id`` will show
        the message 'hello world'. Usually though this is achieved by connecting to the
        socket serving up the VDOM with a query parameter for view ID. This allow many
        views to be added and then displayed dynamically in, for example, a Jupyter
        Notebook where one might want multiple active views which can all be interacted
        with at the same time.

        Refer to :func:`idom.server.imperative_server_mount` for a reference usage.
    """
    next_view_id: Var[int] = Var(0)
    views: Dict[str, ElementConstructor] = {}

    def mount(constructor: ElementConstructor, *args: Any, **kwargs: Any) -> str:
        view_id = next_view_id.get()
        views[str(view_id)] = lambda: constructor(*args, **kwargs)
        next_view_id.set(view_id + 1)
        return str(view_id)

    @element
    async def MultiView(self: Element, view_id: str) -> Any:
        return views[view_id]()

    return mount, MultiView
