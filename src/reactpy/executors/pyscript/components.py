from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from reactpy import component, hooks
from reactpy.executors.pyscript.utils import pyscript_component_html
from reactpy.types import Component, Key
from reactpy.utils import string_to_reactpy

if TYPE_CHECKING:
    from reactpy.types import VdomDict


@component
def _pyscript_component(
    *file_paths: str | Path,
    initial: str | VdomDict = "",
    root: str = "root",
) -> None | VdomDict:
    if not file_paths:
        raise ValueError("At least one file path must be provided.")

    rendered, set_rendered = hooks.use_state(False)
    initial = string_to_reactpy(initial) if isinstance(initial, str) else initial

    if not rendered:
        # FIXME: This is needed to properly re-render PyScript during a WebSocket
        # disconnection / reconnection. There may be a better way to do this in the future.
        set_rendered(True)
        return None

    component_vdom = string_to_reactpy(
        pyscript_component_html(tuple(str(fp) for fp in file_paths), initial, root)
    )
    component_vdom["tagName"] = ""
    return component_vdom


def pyscript_component(
    *file_paths: str | Path,
    initial: str | VdomDict | Component = "",
    root: str = "root",
    key: Key | None = None,
) -> Component:
    """
    Args:
        file_paths: File path to your client-side ReactPy component. If multiple paths are \
            provided, the contents are automatically merged.

    Kwargs:
        initial: The initial HTML that is displayed prior to the PyScript component \
            loads. This can either be a string containing raw HTML, a \
            `#!python reactpy.html` snippet, or a non-interactive component.
        root: The name of the root component function.
    """
    return _pyscript_component(
        *file_paths,
        initial=initial,
        root=root,
        key=key,
    )
