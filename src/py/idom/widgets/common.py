from typing import Any, Callable, Dict, List, Tuple, Optional

import idom
from idom.core import ElementConstructor, Element, element


def node(tag: str, *children: Any, **attributes: Any) -> Dict[str, Any]:
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
    current_root: idom.Var[Optional[Element]] = idom.Var(None)
    current_swap: idom.Var[Callable[[], Any]] = idom.Var(lambda: {"tagName": "div"})
    last_element: idom.Var[Optional[Element]] = idom.Var(None)

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
