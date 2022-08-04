from __future__ import annotations

from base64 import b64encode
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
    TypeVar,
    Union,
)

from typing_extensions import Protocol

import idom

from . import html
from .core import hooks
from .core.component import component
from .core.types import ComponentConstructor, VdomDict
from .utils import Ref


def image(
    format: str,
    value: Union[str, bytes] = "",
    attributes: Optional[Dict[str, Any]] = None,
) -> VdomDict:
    """Utility for constructing an image from a string or bytes

    The source value will automatically be encoded to base64
    """
    if format == "svg":
        format = "svg+xml"

    if isinstance(value, str):
        bytes_value = value.encode()
    else:
        bytes_value = value

    base64_value = b64encode(bytes_value).decode()
    src = f"data:image/{format};base64,{base64_value}"

    return {"tagName": "img", "attributes": {"src": src, **(attributes or {})}}


_Value = TypeVar("_Value")


def use_linked_inputs(
    attributes: Sequence[Dict[str, Any]],
    on_change: Callable[[_Value], None] = lambda value: None,
    cast: _CastFunc[_Value] = lambda value: value,
    initial_value: str = "",
    ignore_empty: bool = True,
) -> List[VdomDict]:
    """Return a list of linked inputs equal to the number of given attributes.

    Parameters:
        attributes:
            That attributes of each returned input element. If the number of generated
            inputs is variable, you may need to assign each one a
            :ref:`key <Organizing Items With Keys>` by including a ``"key"`` in each
            attribute dictionary.
        on_change:
            A callback which is triggered when any input is changed. This callback need
            not update the 'value' field in the attributes of the inputs since that is
            handled automatically.
        cast:
            Cast the 'value' of changed inputs that is passed to ``on_change``.
        initial_value:
            Initialize the 'value' field of the inputs.
        ignore_empty:
            Do not trigger ``on_change`` if the 'value' is an empty string.
    """
    value, set_value = idom.hooks.use_state(initial_value)

    def sync_inputs(event: Dict[str, Any]) -> None:
        new_value = event["target"]["value"]
        set_value(new_value)
        if not new_value and ignore_empty:
            return None
        on_change(cast(new_value))

    inputs: list[VdomDict] = []
    for attrs in attributes:
        # we're going to mutate this so copy it
        attrs = attrs.copy()

        key = attrs.pop("key", None)
        attrs.update({"onChange": sync_inputs, "value": value})

        inputs.append(html.input(attrs, key=key))

    return inputs


_CastTo = TypeVar("_CastTo", covariant=True)


class _CastFunc(Protocol[_CastTo]):
    def __call__(self, value: str) -> _CastTo:
        ...


MountFunc = Callable[["Callable[[], Any] | None"], None]


def hotswap(update_on_change: bool = False) -> Tuple[MountFunc, ComponentConstructor]:
    """Swap out components from a layout on the fly.

    Since you can't change the component functions used to create a layout
    in an imperative manner, you can use ``hotswap`` to do this so
    long as you set things up ahead of time.

    Parameters:
        update_on_change: Whether or not all views of the layout should be udpated on a swap.

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
    constructor_ref: Ref[Callable[[], Any]] = Ref(lambda: None)

    if update_on_change:
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

        def swap(constructor: Callable[[], Any] | None) -> None:
            constructor = constructor_ref.current = constructor or (lambda: None)

            for set_constructor in set_constructor_callbacks:
                set_constructor(constructor)

            return None

    else:

        @component
        def HotSwap() -> Any:
            return constructor_ref.current()

        def swap(constructor: Callable[[], Any] | None) -> None:
            constructor_ref.current = constructor or (lambda: None)
            return None

    return swap, HotSwap


_Func = Callable[..., Any]


def _use_callable(initial_func: _Func) -> Tuple[_Func, Callable[[_Func], None]]:
    state = hooks.use_state(lambda: initial_func)
    return state[0], lambda new: state[1](lambda old: new)
