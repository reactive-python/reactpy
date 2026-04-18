# ruff: noqa: S603
from __future__ import annotations

import base64
import csv
import functools
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import textwrap
from collections.abc import Callable
from importlib import metadata
from io import StringIO
from logging import getLogger
from pathlib import Path
from typing import TYPE_CHECKING, Any
from uuid import uuid4
from zipfile import ZIP_DEFLATED, ZipFile

import reactpy
from reactpy.config import REACTPY_DEBUG, REACTPY_PATH_PREFIX
from reactpy.types import VdomDict
from reactpy.utils import reactpy_to_string

if TYPE_CHECKING:
    from collections.abc import Sequence

_logger = getLogger(__name__)

_PYSCRIPT_WHEELS_DIR = "wheels"
_WHEEL_FILENAME_PART_COUNT = 5


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


def pyscript_executor_html(
    file_paths: Sequence[str],
    uuid: str,
    root: str,
    cache_handler: Callable | None = None,
) -> str:
    """Inserts the user's code into the PyScript template using pattern matching."""
    # Create a valid PyScript executor by replacing the template values
    executor = PYSCRIPT_COMPONENT_TEMPLATE.replace("UUID", uuid)
    executor = executor.replace("return root()", f"return {root}()")

    # Fetch the user's PyScript code
    cache_handler = cache_handler or fetch_cached_python_file
    all_file_contents: list[str] = []
    all_file_contents.extend(cache_handler(file_path) for file_path in file_paths)

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
    modules: dict[str, str] | str | None = None,
    reactpy_pkg_string: str | None = None,
) -> str:
    # Extends ReactPy's default PyScript config with user provided values.
    pyscript_config: dict[str, Any] = {
        "packages": [
            reactpy_pkg_string or _reactpy_pkg_string(),
            "jsonpointer==3.*",
            "ssl",
        ],
        "js_modules": {
            "main": modules
            or {
                f"{REACTPY_PATH_PREFIX.current}static/morphdom/morphdom-esm.js": "morphdom"
            }
        },
    }
    pyscript_config["packages"].extend(extra_py)

    # FIXME: https://github.com/pyscript/pyscript/issues/2282
    if any(pkg.endswith(".whl") for pkg in pyscript_config["packages"]):  # nocov
        pyscript_config["packages_cache"] = "never"

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
    return json.dumps(pyscript_config)


def _reactpy_pkg_string() -> str:
    wheel_file = _ensure_local_reactpy_wheel()
    return (
        f"{REACTPY_PATH_PREFIX.current}static/{_PYSCRIPT_WHEELS_DIR}/{wheel_file.name}"
    )


def _ensure_local_reactpy_wheel() -> Path:
    packaged_wheel = _find_current_reactpy_wheel(_packaged_reactpy_wheels_dir())

    if _source_checkout_exists():
        if packaged_wheel and not _wheel_is_stale_for_source(packaged_wheel):
            return packaged_wheel

        if built_wheel := _build_reactpy_wheel_from_source():
            return _copy_reactpy_wheel_to_static_dir(built_wheel)

        raise RuntimeError(
            "ReactPy could not build a local wheel for PyScript. "
            "Ensure Hatch is installed and `hatch build -t wheel` succeeds."
        )

    if packaged_wheel:
        return packaged_wheel

    if rebuilt_wheel := _rebuild_installed_reactpy_wheel():
        return rebuilt_wheel

    raise RuntimeError(
        "ReactPy could not locate or reconstruct a local wheel for PyScript."
    )


def _source_checkout_exists() -> bool:
    return (_reactpy_repo_root() / "pyproject.toml").exists()


def _reactpy_repo_root() -> Path:
    return Path(reactpy.__file__).resolve().parent.parent.parent


def _packaged_reactpy_wheels_dir() -> Path:
    return Path(reactpy.__file__).resolve().parent / "static" / _PYSCRIPT_WHEELS_DIR


def _find_current_reactpy_wheel(directory: Path) -> Path | None:
    if not directory.exists():
        return None

    matches = sorted(
        path
        for path in directory.glob("reactpy-*.whl")
        if _wheel_matches_local_version(path)
    )
    return matches[0] if matches else None


def _wheel_matches_local_version(path: Path) -> bool:
    name_parts = path.name.removesuffix(".whl").split("-")
    return (
        len(name_parts) >= _WHEEL_FILENAME_PART_COUNT
        and name_parts[0].replace("_", "-").lower() == "reactpy"
        and _normalize_wheel_part(name_parts[1])
        == _normalize_wheel_part(reactpy.__version__)
    )


def _normalize_wheel_part(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value).lower()


def _wheel_is_stale_for_source(wheel_file: Path) -> bool:
    wheel_mtime = wheel_file.stat().st_mtime
    repo_root = _reactpy_repo_root()
    watched_paths = [repo_root / "pyproject.toml", repo_root / "src" / "reactpy"]

    for path in watched_paths:
        if path.is_file() and path.stat().st_mtime > wheel_mtime:
            return True
        if path.is_dir():
            for child in path.rglob("*"):
                if not child.is_file():
                    continue
                if child.suffix == ".pyc" or "__pycache__" in child.parts:
                    continue
                if _packaged_reactpy_wheels_dir() in child.parents:
                    continue
                if child.stat().st_mtime > wheel_mtime:
                    return True

    return False


def _build_reactpy_wheel_from_source() -> Path | None:
    repo_root = _reactpy_repo_root()
    hatch_build_command = _hatch_build_command(repo_root)

    if not hatch_build_command:
        _logger.error("Could not locate Hatch while building a local ReactPy wheel.")
        return None

    _logger.warning("Attempting to build a local wheel for ReactPy...")

    env = os.environ.copy()
    for key in tuple(env):
        if key.startswith("HATCH_ENV_"):
            env.pop(key)

    try:
        result = subprocess.run(
            hatch_build_command,
            capture_output=True,
            text=True,
            check=False,
            cwd=repo_root,
            env=env,
        )
    except OSError:
        _logger.exception(
            "Failed to invoke Hatch while building a local ReactPy wheel."
        )
        return None

    if result.returncode != 0:
        _logger.error(
            "Failed to build a local ReactPy wheel.\nstdout:\n%s\nstderr:\n%s",
            result.stdout,
            result.stderr,
        )
        return None

    dist_dir = repo_root / "dist"
    return _find_current_reactpy_wheel(dist_dir)


def _hatch_build_command(repo_root: Path) -> list[str] | None:
    for candidate in (
        repo_root / ".venv" / "Scripts" / "hatch.exe",
        repo_root / ".venv" / "bin" / "hatch",
    ):
        if candidate.exists():
            return [str(candidate), "build", "-t", "wheel"]

    if hatch_command := shutil.which("hatch"):
        return [hatch_command, "build", "-t", "wheel"]

    if importlib.util.find_spec("hatch") is not None:
        return [sys.executable, "-m", "hatch", "build", "-t", "wheel"]

    return None


def _copy_reactpy_wheel_to_static_dir(wheel_file: Path) -> Path:
    static_wheels_dir = _packaged_reactpy_wheels_dir()
    static_wheels_dir.mkdir(parents=True, exist_ok=True)
    static_wheel = static_wheels_dir / wheel_file.name

    for existing in static_wheels_dir.glob("reactpy-*.whl"):
        if existing != static_wheel:
            existing.unlink()

    if wheel_file.resolve() == static_wheel.resolve():
        return static_wheel

    temp_wheel = static_wheel.with_suffix(f"{static_wheel.suffix}.tmp")
    shutil.copy2(wheel_file, temp_wheel)
    temp_wheel.replace(static_wheel)
    return static_wheel


def _wheel_archive_name(file_path: Path) -> str | None:
    if file_path.is_absolute() or ".." in file_path.parts:
        return None

    return file_path.as_posix()


def _rebuild_installed_reactpy_wheel() -> Path | None:
    try:
        distribution = metadata.distribution("reactpy")
    except metadata.PackageNotFoundError:
        _logger.exception("Could not inspect the installed ReactPy distribution.")
        return None

    files = distribution.files or []
    if not files:
        _logger.error("The installed ReactPy distribution did not expose any files.")
        return None

    static_wheels_dir = _packaged_reactpy_wheels_dir()
    static_wheels_dir.mkdir(parents=True, exist_ok=True)

    wheel_path = static_wheels_dir / _installed_wheel_name(files, distribution)
    temp_wheel_path = wheel_path.with_suffix(".tmp")

    record_rows: list[tuple[str, str, str]] = []
    record_name = _installed_wheel_record_name(files)

    with ZipFile(temp_wheel_path, "w", compression=ZIP_DEFLATED) as wheel_zip:
        for file in files:
            file_path = Path(str(file))
            archive_name = _wheel_archive_name(file_path)
            if archive_name is None:
                _logger.warning(
                    "Skipping installed path '%s' while reconstructing local ReactPy wheel.",
                    file_path.as_posix(),
                )
                continue

            if archive_name == record_name:
                continue

            absolute_path = Path(str(distribution.locate_file(file)))
            if not absolute_path.is_file():
                continue

            file_data = absolute_path.read_bytes()
            wheel_zip.writestr(archive_name, file_data)
            record_rows.append(_record_row(archive_name, file_data))

        record_rows.append((record_name, "", ""))
        wheel_zip.writestr(record_name, _record_text(record_rows))

    temp_wheel_path.replace(wheel_path)
    _logger.warning(
        "PyScript will utilize reconstructed local wheel '%s'.", wheel_path.name
    )
    return wheel_path


def _installed_wheel_name(
    files: Sequence[metadata.PackagePath],
    distribution: metadata.Distribution,
) -> str:
    return (
        f"reactpy-{reactpy.__version__}-{_installed_wheel_tag(files, distribution)}.whl"
    )


def _installed_wheel_tag(
    files: Sequence[metadata.PackagePath],
    distribution: metadata.Distribution,
) -> str:
    wheel_file = next(
        (file for file in files if Path(str(file)).name == "WHEEL"),
        None,
    )
    if not wheel_file:
        return "py3-none-any"

    wheel_text = Path(str(distribution.locate_file(wheel_file))).read_text(
        encoding="utf-8"
    )
    return next(
        (
            line.removeprefix("Tag: ").strip()
            for line in wheel_text.splitlines()
            if line.startswith("Tag: ")
        ),
        "py3-none-any",
    )


def _installed_wheel_record_name(files: Sequence[metadata.PackagePath]) -> str:
    if record_file := next(
        (file for file in files if Path(str(file)).name == "RECORD"),
        None,
    ):
        return Path(str(record_file)).as_posix()

    dist_info_dir = next(
        (
            Path(str(file)).parent.as_posix()
            for file in files
            if Path(str(file)).name == "WHEEL"
        ),
        f"reactpy-{reactpy.__version__}.dist-info",
    )
    return f"{dist_info_dir}/RECORD"


def _record_row(path: str, data: bytes) -> tuple[str, str, str]:
    digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=")
    return (path, f"sha256={digest.decode()}", str(len(data)))


def _record_text(rows: Sequence[tuple[str, str, str]]) -> str:
    output = StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerows(rows)
    return output.getvalue()


@functools.cache
def fetch_cached_python_file(file_path: str, minifiy: bool = True) -> str:
    content = Path(file_path).read_text(encoding="utf-8").strip()
    return minify_python(content) if minifiy else content
