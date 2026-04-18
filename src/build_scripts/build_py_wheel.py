# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

from __future__ import annotations

import importlib.util
import logging
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

_logger = logging.getLogger(__name__)
_SKIP_ENV_VAR = "REACTPY_SKIP_PY_WHEEL_BUILD"


def _reactpy_version(root_dir: Path) -> str:
    init_file = root_dir / "src" / "reactpy" / "__init__.py"
    if match := re.search(
        r'^__version__ = "([^"]+)"$',
        init_file.read_text(encoding="utf-8"),
        re.MULTILINE,
    ):
        return match[1]
    raise RuntimeError("Could not determine the current ReactPy version.")


def _matching_reactpy_wheel(dist_dir: Path, version: str) -> Path | None:
    matching_wheels = sorted(
        dist_dir.glob(f"reactpy-{version}-*.whl"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return matching_wheels[0] if matching_wheels else None


def _hatch_command(root_dir: Path, *args: str) -> list[str] | None:
    for candidate in (
        root_dir / ".venv" / "Scripts" / "hatch.exe",
        root_dir / ".venv" / "bin" / "hatch",
    ):
        if candidate.exists():
            return [str(candidate), *args]

    if hatch_command := shutil.which("hatch"):
        return [hatch_command, *args]

    if importlib.util.find_spec("hatch") is not None:
        return [sys.executable, "-m", "hatch", *args]

    return None


def _hatch_build_command(root_dir: Path) -> list[str] | None:
    return _hatch_command(root_dir, "build", "-t", "wheel")


def _without_hatch_env_vars(env: dict[str, str]) -> dict[str, str]:
    cleaned_env = env.copy()
    for key in tuple(cleaned_env):
        if key.startswith("HATCH_ENV_"):
            cleaned_env.pop(key)
    return cleaned_env


def _run_hatch_command(root_dir: Path, command: list[str], failure_message: str) -> int:
    result = subprocess.run(  # noqa: S603
        command,
        capture_output=True,
        text=True,
        check=False,
        cwd=root_dir,
        env=_without_hatch_env_vars(os.environ.copy()),
    )

    if result.returncode != 0:
        _logger.error(
            "%s\nstdout:\n%s\nstderr:\n%s",
            failure_message,
            result.stdout,
            result.stderr,
        )
        return result.returncode

    return 0


def _build_packaged_static_assets(root_dir: Path) -> int:
    hatch_command = _hatch_command(root_dir, "run", "javascript:build")
    if not hatch_command:
        _logger.error("Could not locate Hatch while building packaged static assets.")
        return 1

    return _run_hatch_command(
        root_dir,
        hatch_command,
        "Failed to build packaged static assets.",
    )


def main() -> int:
    if os.environ.get(_SKIP_ENV_VAR):
        print("Skipping local ReactPy wheel build.")  # noqa: T201
        return 0

    root_dir = Path(__file__).parent.parent.parent

    if static_assets_result := _build_packaged_static_assets(root_dir):
        return static_assets_result

    version = _reactpy_version(root_dir)
    static_wheels_dir = root_dir / "src" / "reactpy" / "static" / "wheels"
    dist_dir = root_dir / "dist"
    hatch_build_command = _hatch_build_command(root_dir)

    if not hatch_build_command:
        _logger.error("Could not locate Hatch while building the embedded wheel.")
        return 1

    static_wheels_dir.mkdir(parents=True, exist_ok=True)
    for wheel_file in static_wheels_dir.glob("reactpy-*.whl"):
        wheel_file.unlink()

    os.environ[_SKIP_ENV_VAR] = "1"
    try:
        if wheel_build_result := _run_hatch_command(
            root_dir,
            hatch_build_command,
            "Failed to build the embedded ReactPy wheel.",
        ):
            return wheel_build_result
    finally:
        os.environ.pop(_SKIP_ENV_VAR, None)

    built_wheel = _matching_reactpy_wheel(dist_dir, version)
    if not built_wheel:
        _logger.error("Failed to locate the newly built ReactPy wheel in %s", dist_dir)
        return 1

    shutil.copy2(built_wheel, static_wheels_dir / built_wheel.name)
    print(f"Embedded local ReactPy wheel at '{static_wheels_dir / built_wheel.name}'")  # noqa: T201
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
