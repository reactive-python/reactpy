from typing import Any, Callable, Tuple, Optional, Dict, Union, IO

from idom import client
from idom.core.element import ElementConstructor, Element, element
from idom.core.vdom import VdomDict, ImportSourceDict, make_vdom_constructor
from idom.tools import Var


class Module:
    """A Javascript module

    Parameters:
        name:
            The module's name. If ``install`` or ``source`` are provided omit the ``.js``
            file extension. Otherwise this is the exact import path and could be anything
            including a URL.
        install:
            If a string, then the dependency string used to install a module with
            the given ``name`` (e.g. ``my-module@1.2.3``). If ``True`` then the given
            ``name`` will be used as the dependency string.
        source:
            Create a module of the given name using the given source code.

    Returns:
        An :class:`Import` element for the newly defined module.
    """

    __slots__ = ("_module", "_name", "_installed")

    def __init__(
        self,
        name: str,
        install: Union[bool, str] = False,
        source: Optional[IO] = None,
        replace: bool = False,
    ) -> None:
        self._installed = False
        if install and source:
            raise ValueError("Both 'install' and 'source' were given.")
        elif (install or source) and not replace and client.web_module_exists(name):
            self._module = client.web_module(name)
            self._installed = True
            self._name = name
        elif source is not None:
            client.define_web_module(name, source.read())
            self._module = client.web_module(name)
            self._installed = True
            self._name = name
        elif isinstance(install, str):
            client.install({install: name})
            self._module = client.web_module(name)
            self._installed = True
            self._name = name
        elif install is True:
            client.install({name: name})
            self._module = client.web_module(name)
            self._installed = True
            self._name = name
        else:
            self._module = name

    @property
    def name(self) -> str:
        if not self._installed:
            raise ValueError("Module is not installed locally")
        return self._name

    @property
    def url(self) -> str:
        return self._module

    def Import(self, name: str, *args, **kwargs) -> "Import":
        return Import(self._module, name, *args, **kwargs)

    def delete(self) -> None:
        if not self._installed:
            raise ValueError("Module is not installed locally")
        client.delete_web_module(self._module)

    def __repr__(self) -> str:  # pragma: no cover
        return f"{type(self).__name__}({self._module!r})"


class Import:
    """Import a react module

    Once imported, you can instantiate the library's components by calling them
    via attribute-access.

    Examples:

        .. code-block:: python

            victory = idom.Import("victory", "VictoryBar" install=True)
            style = {"parent": {"width": "500px"}}
            victory.VictoryBar({"style": style}, fallback="loading...")
    """

    __slots__ = ("_constructor", "_import_source")

    def __init__(
        self,
        module: str,
        name: str,
        has_children: bool = True,
        fallback: Optional[str] = "",
    ) -> None:
        self._constructor = make_vdom_constructor(name, has_children)
        self._import_source = ImportSourceDict(source=module, fallback=fallback)

    def __call__(self, *args: Any, **kwargs: Any,) -> VdomDict:
        return self._constructor(import_source=self._import_source, *args, **kwargs)

    def __repr__(self) -> str:  # pragma: no cover
        items = ", ".join(f"{k}={v!r}" for k, v in self._import_source.items())
        return f"{type(self).__name__}({items})"


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
