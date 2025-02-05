from __future__ import annotations

import functools
import json
import textwrap
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import uuid4

import jsonpointer
import orjson

import reactpy
from reactpy.config import REACTPY_DEBUG, REACTPY_PATH_PREFIX
from reactpy.types import VdomDict
from reactpy.utils import vdom_to_html

if TYPE_CHECKING:
    from collections.abc import Sequence


PYSCRIPT_COMPONENT_TEMPLATE = (
    Path(__file__).parent / "component_template.py"
).read_text(encoding="utf-8")
PYSCRIPT_LAYOUT_HANDLER = (Path(__file__).parent / "layout_handler.py").read_text(
    encoding="utf-8"
)


def render_pyscript_executor(file_paths: tuple[str, ...], uuid: str, root: str) -> str:
    """Inserts the user's code into the PyScript template using pattern matching."""
    # Create a valid PyScript executor by replacing the template values
    executor = PYSCRIPT_COMPONENT_TEMPLATE.replace("UUID", uuid)
    executor = executor.replace("return root()", f"return {root}()")

    # Fetch the user's PyScript code
    all_file_contents: list[str] = []
    all_file_contents.extend(cached_file_read(file_path) for file_path in file_paths)

    # Prepare the PyScript code block
    user_code = "\n".join(all_file_contents)  # Combine all user code
    user_code = user_code.replace("\t", "    ")  # Normalize the text
    user_code = textwrap.indent(user_code, "    ")  # Add indentation to match template

    # Insert the user code into the PyScript template
    return executor.replace("    def root(): ...", user_code)


def pyscript_component_html(
    file_paths: tuple[str, ...], initial: str | VdomDict, root: str
) -> str:
    """Renders a PyScript component with the user's code."""
    _initial = initial if isinstance(initial, str) else vdom_to_html(initial)
    uuid = uuid4().hex
    executor_code = render_pyscript_executor(
        file_paths=file_paths, uuid=uuid, root=root
    )

    return (
        f'<div id="pyscript-{uuid}" class="pyscript" data-uuid="{uuid}">'
        f"{_initial}"
        "</div>"
        f"<py-script async>{executor_code}</py-script>"
    )


def pyscript_setup_html(
    extra_py: Sequence[str], extra_js: dict | str, config: dict | str
) -> str:
    """Renders the PyScript setup code."""
    hide_pyscript_debugger = f'<link rel="stylesheet" href="{REACTPY_PATH_PREFIX.current}static/pyscript-hide-debug.css" />'
    pyscript_config = extend_pyscript_config(extra_py, extra_js, config)

    return (
        f'<link rel="stylesheet" href="{REACTPY_PATH_PREFIX.current}static/pyscript/core.css" />'
        f'<link rel="stylesheet" href="{REACTPY_PATH_PREFIX.current}static/pyscript-custom.css" />'
        f"{'' if REACTPY_DEBUG.current else hide_pyscript_debugger}"
        f'<script type="module" async crossorigin="anonymous" src="{REACTPY_PATH_PREFIX.current}static/pyscript/core.js">'
        "</script>"
        f'<py-script async config="{pyscript_config}">{PYSCRIPT_LAYOUT_HANDLER}</py-script>'
    )


def extend_pyscript_config(
    extra_py: Sequence[str], extra_js: dict | str, config: dict | str
) -> str:
    # Extends ReactPy's default PyScript config with user provided values.
    pyscript_config = {
        "packages": [
            f"reactpy=={reactpy.__version__}",
            f"jsonpointer=={jsonpointer.__version__}",
            "ssl",
        ],
        "js_modules": {
            "main": {
                f"{REACTPY_PATH_PREFIX.current}static/morphdom/morphdom-esm.js": "morphdom"
            }
        },
    }
    pyscript_config["packages"].extend(extra_py)

    # Extend the JavaScript dependency list
    if extra_js and isinstance(extra_js, str):
        pyscript_config["js_modules"]["main"].update(json.loads(extra_js))
    elif extra_js and isinstance(extra_js, dict):
        pyscript_config["js_modules"]["main"].update(extra_py)

    # Update other config attributes
    if config and isinstance(config, str):
        pyscript_config.update(json.loads(config))
    elif config and isinstance(config, dict):
        pyscript_config.update(config)
    return orjson.dumps(pyscript_config).decode("utf-8")


@functools.cache
def cached_file_read(file_path: str) -> str:
    return Path(file_path).read_text(encoding="utf-8").strip()
