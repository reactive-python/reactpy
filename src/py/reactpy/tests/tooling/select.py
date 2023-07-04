from __future__ import annotations

from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from typing import Callable

from reactpy.core.types import VdomJson

Selector = Callable[[VdomJson, "ElementInfo"], bool]


def id_equals(id: str) -> Selector:
    return lambda element, _: element.get("attributes", {}).get("id") == id


def class_equals(class_name: str) -> Selector:
    return (
        lambda element, _: class_name
        in element.get("attributes", {}).get("class", "").split()
    )


def text_equals(text: str) -> Selector:
    return lambda element, _: _element_text(element) == text


def _element_text(element: VdomJson) -> str:
    if isinstance(element, str):
        return element
    return "".join(_element_text(child) for child in element.get("children", []))


def element_exists(element: VdomJson, selector: Selector) -> bool:
    return next(find_elements(element, selector), None) is not None


def find_element(
    element: VdomJson,
    selector: Selector,
    *,
    first: bool = False,
) -> tuple[VdomJson, ElementInfo]:
    """Find an element by a selector.

    Parameters:
        element:
            The tree to search.
        selector:
            A function that returns True if the element matches.
        first:
            If True, return the first element found. If False, raise an error if
            multiple elements are found.

    Returns:
        Element info, or None if not found.
    """
    find_iter = find_elements(element, selector)
    found = next(find_iter, None)
    if found is None:
        raise ValueError("Element not found")
    if not first:
        try:
            next(find_iter)
            raise ValueError("Multiple elements found")
        except StopIteration:
            pass
    return found


def find_elements(
    element: VdomJson, selector: Selector
) -> Iterator[tuple[VdomJson, ElementInfo]]:
    """Find an element by a selector.

    Parameters:
        element:
            The tree to search.
        selector:
            A function that returns True if the element matches.

    Returns:
        Element info, or None if not found.
    """
    return _find_elements(element, selector, (), ())


def _find_elements(
    element: VdomJson,
    selector: Selector,
    parents: Sequence[VdomJson],
    path: Sequence[int],
) -> tuple[VdomJson, ElementInfo] | None:
    info = ElementInfo(parents, path)
    if selector(element, info):
        yield element, info

    for index, child in enumerate(element.get("children", [])):
        if isinstance(child, dict):
            yield from _find_elements(
                child, selector, (*parents, element), (*path, index)
            )


@dataclass
class ElementInfo:
    parents: Sequence[VdomJson]
    path: Sequence[int]
