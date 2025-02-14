# ruff: noqa: S603, S607
from __future__ import annotations

import functools
import json
import re
import shutil
import subprocess
import textwrap
from glob import glob
from logging import getLogger
from pathlib import Path
from typing import TYPE_CHECKING, Any
from uuid import uuid4

import jsonpointer

import reactpy
from reactpy.config import REACTPY_DEBUG, REACTPY_PATH_PREFIX, REACTPY_WEB_MODULES_DIR
from reactpy.types import VdomDict
from reactpy.utils import reactpy_to_string

if TYPE_CHECKING:
    from collections.abc import Sequence

_logger = getLogger(__name__)


def minify_python(source: str) -> str:
    """Minify Python source code."""
    # Remove comments
    source = re.sub(r"#.*\n", "\n", source)
    # Remove docstrings
    source = re.sub(r'\n\s*""".*?"""', "", source, flags=re.DOTALL)
    # Remove excess newlines
    source = re.sub(r"\n+", "\n", source)
    # Remove empty lines
    source = re.sub(r"\s+\n", "\n", source)
    # Remove leading and trailing whitespace
    return source.strip()


PYSCRIPT_COMPONENT_TEMPLATE = minify_python(
    (Path(__file__).parent / "component_template.py").read_text(encoding="utf-8")
)
PYSCRIPT_LAYOUT_HANDLER = minify_python(
    (Path(__file__).parent / "layout_handler.py").read_text(encoding="utf-8")
)


def pyscript_executor_html(file_paths: Sequence[str], uuid: str, root: str) -> str:
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

    # Ensure the root component exists
    if f"def {root}():" not in user_code:
        raise ValueError(
            f"Could not find the root component function '{root}' in your PyScript file(s)."
        )

    # Insert the user code into the PyScript template
    return executor.replace("    def root(): ...", user_code)


def pyscript_component_html(
    file_paths: Sequence[str], initial: str | VdomDict, root: str
) -> str:
    """Renders a PyScript component with the user's code."""
    _initial = initial if isinstance(initial, str) else reactpy_to_string(initial)
    uuid = uuid4().hex
    executor_code = pyscript_executor_html(file_paths=file_paths, uuid=uuid, root=root)

    return (
        f'<div id="pyscript-{uuid}" class="pyscript" data-uuid="{uuid}">'
        f"{_initial}"
        "</div>"
        f"<script type='py'>{executor_code}</script>"
    )


def pyscript_setup_html(
    extra_py: Sequence[str],
    extra_js: dict[str, Any] | str,
    config: dict[str, Any] | str,
) -> str:
    """Renders the PyScript setup code."""
    hide_pyscript_debugger = f'<link rel="stylesheet" href="{REACTPY_PATH_PREFIX.current}static/pyscript-hide-debug.css" />'
    pyscript_config = extend_pyscript_config(extra_py, extra_js, config)

    return (
        f'<link rel="stylesheet" href="{REACTPY_PATH_PREFIX.current}static/pyscript/core.css" />'
        f"{'' if REACTPY_DEBUG.current else hide_pyscript_debugger}"
        f'<script type="module" async crossorigin="anonymous" src="{REACTPY_PATH_PREFIX.current}static/pyscript/core.js">'
        "</script>"
        f"<script type='py' config='{pyscript_config}'>{PYSCRIPT_LAYOUT_HANDLER}</script>"
    )


def extend_pyscript_config(
    extra_py: Sequence[str],
    extra_js: dict[str, str] | str,
    config: dict[str, Any] | str,
) -> str:
    import orjson

    # Extends ReactPy's default PyScript config with user provided values.
    pyscript_config: dict[str, Any] = {
        "packages": [
            reactpy_version_string(),
            f"jsonpointer=={jsonpointer.__version__}",
            "ssl",
        ],
        "js_modules": {
            "main": {
                f"{REACTPY_PATH_PREFIX.current}static/morphdom/morphdom-esm.js": "morphdom"
            }
        },
        "packages_cache": "never",
    }
    pyscript_config["packages"].extend(extra_py)

    # Extend the JavaScript dependency list
    if extra_js and isinstance(extra_js, str):
        pyscript_config["js_modules"]["main"].update(json.loads(extra_js))
    elif extra_js and isinstance(extra_js, dict):
        pyscript_config["js_modules"]["main"].update(extra_js)

    # Update other config attributes
    if config and isinstance(config, str):
        pyscript_config.update(json.loads(config))
    elif config and isinstance(config, dict):
        pyscript_config.update(config)
    return orjson.dumps(pyscript_config).decode("utf-8")


def reactpy_version_string() -> str:  # nocov
    from reactpy.testing.common import GITHUB_ACTIONS

    local_version = reactpy.__version__

    # Get a list of all versions via `pip index versions`
    result = cached_pip_index_versions("reactpy")

    # Check if the command failed
    if result.returncode != 0:
        _logger.warning(
            "Failed to verify what versions of ReactPy exist on PyPi. "
            "PyScript functionality may not work as expected.",
        )
        return f"reactpy=={local_version}"

    # Have `pip` tell us what versions are available
    available_version_symbol = "Available versions: "
    latest_version_symbol = "LATEST: "
    known_versions: list[str] = []
    latest_version: str = ""
    for line in result.stdout.splitlines():
        if line.startswith(available_version_symbol):
            known_versions.extend(line[len(available_version_symbol) :].split(", "))
        elif latest_version_symbol in line:
            symbol_postion = line.index(latest_version_symbol)
            latest_version = line[symbol_postion + len(latest_version_symbol) :].strip()

    # Return early if the version is available on PyPi and we're not in a CI environment
    if local_version in known_versions and not GITHUB_ACTIONS:
        return f"reactpy=={local_version}"

    # We are now determining an alternative method of installing ReactPy for PyScript
    if not GITHUB_ACTIONS:
        _logger.warning(
            "Your current version of ReactPy isn't available on PyPi. Since a packaged version "
            "of ReactPy is required for PyScript, we are attempting to find an alternative method..."
        )

    # Build a local wheel for ReactPy, if needed
    dist_dir = Path(reactpy.__file__).parent.parent.parent / "dist"
    wheel_glob = glob(str(dist_dir / f"reactpy-{local_version}-*.whl"))
    if not wheel_glob:
        _logger.warning("Attempting to build a local wheel for ReactPy...")
        subprocess.run(
            ["hatch", "build", "-t", "wheel"],
            capture_output=True,
            text=True,
            check=False,
            cwd=Path(reactpy.__file__).parent.parent.parent,
        )
    wheel_glob = glob(str(dist_dir / f"reactpy-{local_version}-*.whl"))

    # Building a local wheel failed, try our best to give the user any possible version.
    if not wheel_glob:
        if latest_version:
            _logger.warning(
                "Failed to build a local wheel for ReactPy, likely due to missing build dependencies. "
                "PyScript will default to using the latest ReactPy version on PyPi."
            )
            return f"reactpy=={latest_version}"
        _logger.error(
            "Failed to build a local wheel for ReactPy, and could not determine the latest version on PyPi. "
            "PyScript functionality may not work as expected.",
        )
        return f"reactpy=={local_version}"

    # Move the local wheel file to the web modules directory, if needed
    wheel_file = Path(wheel_glob[0])
    new_path = REACTPY_WEB_MODULES_DIR.current / wheel_file.name
    if not new_path.exists():
        _logger.warning(
            "PyScript will utilize local wheel '%s'.",
            wheel_file.name,
        )
        shutil.copy(wheel_file, new_path)
    return f"{REACTPY_PATH_PREFIX.current}modules/{wheel_file.name}"


@functools.cache
def cached_pip_index_versions(package_name: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["pip", "index", "versions", package_name],
        capture_output=True,
        text=True,
        check=False,
    )


@functools.cache
def cached_file_read(file_path: str, minifiy: bool = True) -> str:
    content = Path(file_path).read_text(encoding="utf-8").strip()
    return minify_python(content) if minifiy else content
