from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path
from unittest import mock


def _load_build_py_wheel_module():
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "build_scripts"
        / "build_py_wheel.py"
    )
    spec = importlib.util.spec_from_file_location("build_py_wheel", module_path)
    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_text(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_hatch_build_command_uses_python_module_when_available(tmp_path):
    build_py_wheel = _load_build_py_wheel_module()

    with (
        mock.patch.object(build_py_wheel.shutil, "which", return_value=None),
        mock.patch.object(
            build_py_wheel.importlib.util,
            "find_spec",
            return_value=object(),
        ),
    ):
        assert build_py_wheel._hatch_build_command(tmp_path) == [
            build_py_wheel.sys.executable,
            "-m",
            "hatch",
            "build",
            "-t",
            "wheel",
        ]


def test_build_packaged_static_assets_runs_javascript_build(tmp_path):
    build_py_wheel = _load_build_py_wheel_module()

    with (
        mock.patch.object(build_py_wheel.shutil, "which", return_value=None),
        mock.patch.object(
            build_py_wheel.importlib.util,
            "find_spec",
            return_value=object(),
        ),
        mock.patch.object(build_py_wheel.subprocess, "run") as run,
    ):
        run.return_value = subprocess.CompletedProcess([], 0, "built", "")

        assert build_py_wheel._build_packaged_static_assets(tmp_path) == 0

    run.assert_called_once()
    assert run.call_args.args[0] == [
        build_py_wheel.sys.executable,
        "-m",
        "hatch",
        "run",
        "javascript:build",
    ]


def test_main_skips_all_work_when_skip_env_var_is_set(tmp_path):
    build_py_wheel = _load_build_py_wheel_module()
    build_script = _write_text(
        tmp_path / "src" / "build_scripts" / "build_py_wheel.py",
        "",
    )

    with (
        mock.patch.object(build_py_wheel, "__file__", str(build_script)),
        mock.patch.object(
            build_py_wheel, "_build_packaged_static_assets"
        ) as build_static_assets,
        mock.patch.dict(
            build_py_wheel.os.environ,
            {build_py_wheel._SKIP_ENV_VAR: "1"},
            clear=False,
        ),
    ):
        assert build_py_wheel.main() == 0

    build_static_assets.assert_not_called()


def test_main_builds_static_assets_before_embedded_wheel(tmp_path):
    build_py_wheel = _load_build_py_wheel_module()
    build_script = _write_text(
        tmp_path / "src" / "build_scripts" / "build_py_wheel.py",
        "",
    )
    built_wheel = _write_text(
        tmp_path / "dist" / "reactpy-2.0.0b11-py3-none-any.whl",
        "wheel",
    )
    steps: list[str] = []

    with (
        mock.patch.object(build_py_wheel, "__file__", str(build_script)),
        mock.patch.object(
            build_py_wheel,
            "_build_packaged_static_assets",
            side_effect=lambda root_dir: steps.append("javascript") or 0,
        ),
        mock.patch.object(
            build_py_wheel,
            "_reactpy_version",
            return_value="2.0.0b11",
        ),
        mock.patch.object(
            build_py_wheel,
            "_hatch_build_command",
            return_value=["hatch", "build", "-t", "wheel"],
        ),
        mock.patch.object(
            build_py_wheel,
            "_run_hatch_command",
            side_effect=lambda root_dir, command, message: steps.append("wheel") or 0,
        ),
        mock.patch.object(
            build_py_wheel,
            "_matching_reactpy_wheel",
            return_value=built_wheel,
        ),
    ):
        assert build_py_wheel.main() == 0

    assert steps == ["javascript", "wheel"]
