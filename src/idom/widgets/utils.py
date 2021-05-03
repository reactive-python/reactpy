"""
Widget Tools
============
"""
from __future__ import annotations

from typing import Any, Callable, Dict, Optional, Set, Tuple, TypeVar

from idom.core import hooks
from idom.core.component import ComponentConstructor, component
from idom.utils import Ref


MountFunc = Callable[[ComponentConstructor], None]


def hotswap(shared: bool = False) -> Tuple[MountFunc, ComponentConstructor]:
    """Swap out components from a layout on the fly.

    Since you can't change the component functions used to create a layout
    in an imperative manner, you can use ``hotswap`` to do this so
    long as you set things up ahead of time.

    Parameters:
        shared: Whether or not all views of the layout should be udpated on a swap.

    Example:
        .. code-block:: python

            import idom

            show, root = idom.hotswap()
            PerClientStateServer(root).run_in_thread("localhost", 8765)

            @idom.component
            def DivOne(self):
                return {"tagName": "div", "children": [1]}

            show(DivOne)

            # displaying the output now will show DivOne

            @idom.component
            def DivTwo(self):
                return {"tagName": "div", "children": [2]}

            show(DivTwo)

            # displaying the output now will show DivTwo
    """
    constructor_ref: Ref[Callable[[], Any]] = Ref(lambda: {"tagName": "div"})

    if shared:
        set_constructor_callbacks: Set[Callable[[Callable[[], Any]], None]] = set()

        @component
        def HotSwap() -> Any:
            # new displays will adopt the latest constructor and arguments
            constructor, set_constructor = _use_callable(constructor_ref.current)

            def add_callback() -> Callable[[], None]:
                set_constructor_callbacks.add(set_constructor)
                return lambda: set_constructor_callbacks.remove(set_constructor)

            hooks.use_effect(add_callback)

            return constructor()

        def swap(constructor: Callable[[], Any]) -> None:
            constructor_ref.current = constructor

            for set_constructor in set_constructor_callbacks:
                set_constructor(constructor)

            return None

    else:

        @component
        def HotSwap() -> Any:
            return constructor_ref.current()

        def swap(constructor: Callable[[], Any]) -> None:
            constructor_ref.current = constructor
            return None

    return swap, HotSwap


_Func = Callable[..., Any]
_FuncVar = TypeVar("_FuncVar", bound=_Func)


def _use_callable(initial_func: _FuncVar) -> Tuple[_FuncVar, Callable[[_Func], None]]:
    state: Tuple[_FuncVar, Callable[[_Func], None]] = hooks.use_state(
        lambda: initial_func
    )
    return state[0], lambda new: state[1](lambda old: new)


def multiview() -> Tuple[MultiViewMount, ComponentConstructor]:
    """Dynamically add components to a layout on the fly

    Since you can't change the component functions used to create a layout
    in an imperative manner, you can use ``multiview`` to do this so
    long as you set things up ahead of time.

    Examples:

        .. code-block::

            import idom

            mount, multiview = idom.widgets.multiview()

            @idom.component
            def Hello():
                return idom.html.h1(["hello"])

            # auto static view ID
            mount.add("hello", Hello)
            # use the view ID to create the associate component instance
            hello_component_instance = multiview("hello")

            @idom.component
            def World():
                return idom.html.h1(["world"])

            generated_view_id = mount.add(None, World)
            world_component_instance = multiview(generated_view_id)

        Displaying ``root`` with the parameter ``view_id=hello_world_view_id`` will show
        the message 'hello world'. Usually though this is achieved by connecting to the
        socket serving up the VDOM with a query parameter for view ID. This allow many
        views to be added and then displayed dynamically in, for example, a Jupyter
        Notebook where one might want multiple active views which can all be interacted
        with at the same time.

        Refer to :func:`idom.server.imperative_server_mount` for a reference usage.
    """
    views: Dict[str, ComponentConstructor] = {}

    @component
    def MultiView(view_id: str) -> Any:
        return views[view_id]()

    return MultiViewMount(views), MultiView


class MultiViewMount:
    """Mount point for :func:`multiview`"""

    __slots__ = "_next_auto_id", "_views"

    def __init__(self, views: Dict[str, ComponentConstructor]):
        self._next_auto_id = 0
        self._views = views

    def add(self, view_id: Optional[str], constructor: ComponentConstructor) -> str:
        """Add a component constructor

        Parameters:
            view_id:
                The view ID the constructor will be associated with. If ``None`` then
                a view ID will be automatically generated.
            constructor:
                The component constructor to be mounted. It must accept no arguments.

        Returns:
            The view ID that was assocaited with the component - most useful for
            auto-generated view IDs
        """
        if view_id is None:
            self._next_auto_id += 1
            view_id = str(self._next_auto_id)
        self._views[view_id] = constructor
        return view_id

    def remove(self, view_id: str) -> None:
        """Remove a mounted component constructor given its view ID"""
        del self._views[view_id]

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self._views})"
