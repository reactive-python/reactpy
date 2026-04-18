from __future__ import annotations

import importlib.util
from pathlib import Path
from unittest import mock


def _load_build_local_wheel_module():
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "build_scripts"
        / "build_local_wheel.py"
    )
    spec = importlib.util.spec_from_file_location("build_local_wheel", module_path)
    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_hatch_build_command_uses_python_module_when_available(tmp_path):
    build_local_wheel = _load_build_local_wheel_module()

    with (
        mock.patch.object(build_local_wheel.shutil, "which", return_value=None),
        mock.patch.object(
            build_local_wheel.importlib.util,
            "find_spec",
            return_value=object(),
        ),
    ):
        assert build_local_wheel._hatch_build_command(tmp_path) == [
            build_local_wheel.sys.executable,
            "-m",
            "hatch",
            "build",
            "-t",
            "wheel",
        ]
