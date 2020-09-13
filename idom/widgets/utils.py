from typing import Any, Callable, Tuple, Dict, Set, cast

from typing_extensions import Protocol

from idom.core import hooks
from idom.core.element import ElementConstructor, element
from idom.utils import Ref


class MountFunc(Protocol):
    """Function for mounting views"""

    def __call__(
        self, constructor: ElementConstructor, *args: Any, **kwargs: Any
    ) -> Any:
        ...


_FuncArgsKwargs = Tuple[Callable[..., Any], Tuple[Any, ...], Dict[str, Any]]


def hotswap(shared: bool = False) -> Tuple[MountFunc, ElementConstructor]:
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
    constructor_and_arguments: Ref[_FuncArgsKwargs] = Ref(
        (lambda: {"tagName": "div"}, (), {})
    )

    if shared:
        set_state_callbacks: Set[Callable[[_FuncArgsKwargs], None]] = set()

        @element
        def HotSwap() -> Any:
            # new displays will adopt the latest constructor and arguments
            (f, a, kw), set_state = hooks.use_state(constructor_and_arguments.current)

            def add_callback() -> Callable[[], None]:
                set_state_callbacks.add(set_state)
                return lambda: set_state_callbacks.remove(set_state)

            hooks.use_effect(add_callback)

            return f(*a, **kw)

        def swap(_func_: ElementConstructor, *args: Any, **kwargs: Any) -> None:
            f_a_kw = constructor_and_arguments.current = (_func_, args, kwargs)

            for set_state in set_state_callbacks:
                set_state(f_a_kw)

            return None

    else:

        @element
        def HotSwap() -> Any:
            func, args, kwargs = constructor_and_arguments.current
            return func(*args, **kwargs)

        def swap(_func_: ElementConstructor, *args: Any, **kwargs: Any) -> None:
            constructor_and_arguments.current = (_func_, args, kwargs)
            return None

    return cast(MountFunc, swap), HotSwap


def multiview() -> Tuple["MultiViewMount", ElementConstructor]:
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
    views: Dict[str, ElementConstructor] = {}

    @element
    def MultiView(view_id: str) -> Any:
        return views[view_id]()

    return MultiViewMount(views), MultiView


class MultiViewMount:

    __slots__ = "_next_auto_id", "_views"

    def __init__(self, views: Dict[str, ElementConstructor]):
        self._next_auto_id = 0
        self._views = views

    def remove(self, view_id: str) -> None:
        del self._views[view_id]

    def __getitem__(self, view_id: str) -> MountFunc:
        def mount(constructor: ElementConstructor, *args: Any, **kwargs: Any) -> str:
            self._add_view(view_id, constructor, args, kwargs)
            return view_id

        return mount

    def __call__(
        self, constructor: ElementConstructor, *args: Any, **kwargs: Any
    ) -> str:
        self._next_auto_id += 1
        view_id = str(self._next_auto_id)
        self._add_view(view_id, constructor, args, kwargs)
        return view_id

    def _add_view(
        self,
        view_id: str,
        constructor: ElementConstructor,
        args: Tuple[Any, ...],
        kwargs: Dict[str, Any],
    ) -> None:
        self._views[view_id] = lambda: constructor(*args, **kwargs)
