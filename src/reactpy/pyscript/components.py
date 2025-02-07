from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

from reactpy import component, hooks, html
from reactpy.pyscript.utils import render_pyscript_executor
from reactpy.types import ComponentType
from reactpy.utils import vdom_to_html

if TYPE_CHECKING:
    from reactpy.types import VdomDict


@component
def _pyscript_component(
    *file_paths: str,
    initial: str | VdomDict = "",
    root: str = "root",
) -> None | VdomDict:
    if not file_paths:
        raise ValueError("At least one file path must be provided.")

    rendered, set_rendered = hooks.use_state(False)
    uuid = hooks.use_ref(uuid4().hex.replace("-", "")).current
    initial = initial if isinstance(initial, str) else vdom_to_html(initial)
    executor = render_pyscript_executor(file_paths=file_paths, uuid=uuid, root=root)

    if not rendered:
        # FIXME: This is needed to properly re-render PyScript during a WebSocket
        # disconnection / reconnection. There may be a better way to do this in the future.
        set_rendered(True)
        return None

    return html.fragment(
        html.div(
            {"id": f"pyscript-{uuid}", "className": "pyscript", "data-uuid": uuid},
            initial,
        ),
        html.py_script(executor),
    )


def pyscript_component(
    *file_paths: str,
    initial: str | VdomDict | ComponentType = "",
    root: str = "root",
) -> ComponentType:
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
    )
