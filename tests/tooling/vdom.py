from __future__ import annotations

from typing import Callable, Iterator, TypeVar

from idom.core.types import VdomDict, VdomJson


_Element = TypeVar("_Element", bound="VdomDict | VdomJson")


def find_vdom(vdom: _Element, match: Callable[[_Element], bool]) -> list[_Element]:
    return list(_find_vdom(vdom, match))


def _find_vdom(vdom: _Element, match: Callable[[_Element], bool]) -> Iterator[_Element]:
    if match(vdom):
        yield vdom
    for child in vdom.get("children", []):
        if isinstance(child, dict):
            yield from _find_vdom(child, match)
