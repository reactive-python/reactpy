import os
from pathlib import Path
from unittest import mock
from uuid import uuid4
from zipfile import ZipFile

import orjson
import pytest

from reactpy.config import REACTPY_PATH_PREFIX
from reactpy.executors.pyscript import utils
from reactpy.testing import assert_reactpy_did_log


class _FakeDistribution:
    def __init__(self, root: Path, files: list[Path | str]) -> None:
        self._root = root
        self.files = [Path(file) for file in files]

    def locate_file(self, file: Path | str) -> Path:
        return self._root / Path(str(file))


def _write_file(path: Path, content: str, mtime: int | None = None) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    if mtime is not None:
        os.utime(path, (mtime, mtime))
    return path


def _current_wheel_name() -> str:
    return f"reactpy-{utils.reactpy.__version__}-py3-none-any.whl"


def _current_wheel_path(*parts: str) -> Path:
    return Path(*parts, _current_wheel_name()) if parts else Path(_current_wheel_name())


def test_bad_root_name():
    file_path = str(
        Path(__file__).parent / "pyscript_components" / "custom_root_name.py"
    )

    with pytest.raises(ValueError):
        utils.pyscript_executor_html((file_path,), uuid4().hex, "bad")


def test_pyscript_component_html_renders_executor_markup():
    with (
        mock.patch(
            "reactpy.executors.pyscript.utils.reactpy_to_string",
            return_value="<p>initial</p>",
        ),
        mock.patch(
            "reactpy.executors.pyscript.utils.pyscript_executor_html",
            return_value="print('hello')",
        ) as executor_html,
        mock.patch(
            "reactpy.executors.pyscript.utils.uuid4",
            return_value=mock.Mock(hex="abc123"),
        ),
    ):
        html = utils.pyscript_component_html(
            file_paths=("app.py",),
            initial={"tagName": "div"},
            root="root",
        )

    executor_html.assert_called_once_with(
        file_paths=("app.py",),
        uuid="abc123",
        root="root",
    )
    assert html == (
        '<div id="pyscript-abc123" class="pyscript" data-uuid="abc123">'
        "<p>initial</p>"
        "</div>"
        "<script type='py'>print('hello')</script>"
    )


def test_pyscript_setup_html_renders_setup_assets():
    with (
        mock.patch.object(utils.REACTPY_DEBUG, "current", False),
        mock.patch(
            "reactpy.executors.pyscript.utils.extend_pyscript_config",
            return_value='{"packages": []}',
        ) as extend_config,
    ):
        html = utils.pyscript_setup_html(["foo"], {"/bar.js": "bar"}, {"x": 1})

    extend_config.assert_called_once_with(["foo"], {"/bar.js": "bar"}, {"x": 1})
    assert (
        f'<link rel="stylesheet" href="{REACTPY_PATH_PREFIX.current}static/pyscript/core.css" />'
        in html
    )
    assert (
        f'<link rel="stylesheet" href="{REACTPY_PATH_PREFIX.current}static/pyscript-hide-debug.css" />'
        in html
    )
    assert (
        f'<script type="module" async crossorigin="anonymous" src="{REACTPY_PATH_PREFIX.current}static/pyscript/core.js">'
        in html
    )
    assert "config='{\"packages\": []}'" in html


def test_extend_pyscript_config():
    extra_py = ["orjson", "tabulate"]
    extra_js = {"/static/foo.js": "bar"}
    config = {"packages_cache": "always"}

    with mock.patch(
        "reactpy.executors.pyscript.utils._reactpy_pkg_string",
        return_value="/reactpy/static/wheels/reactpy-test.whl",
    ):
        result = utils.extend_pyscript_config(extra_py, extra_js, config)
        result = orjson.loads(result)

    # Check whether `packages` have been combined
    assert "orjson" in result["packages"]
    assert "tabulate" in result["packages"]
    assert any("reactpy" in package for package in result["packages"])

    # Check whether `js_modules` have been combined
    assert "/static/foo.js" in result["js_modules"]["main"]
    assert any("morphdom" in module for module in result["js_modules"]["main"])

    # Check whether `packages_cache` has been overridden
    assert result["packages_cache"] == "always"


def test_extend_pyscript_config_string_values():
    extra_py = []
    extra_js = {"/static/foo.js": "bar"}
    config = {"packages_cache": "always"}

    # Try using string based `extra_js` and `config`
    extra_js_string = orjson.dumps(extra_js).decode()
    config_string = orjson.dumps(config).decode()
    with mock.patch(
        "reactpy.executors.pyscript.utils._reactpy_pkg_string",
        return_value="/reactpy/static/wheels/reactpy-test.whl",
    ):
        result = utils.extend_pyscript_config(extra_py, extra_js_string, config_string)
        result = orjson.loads(result)

    # Make sure `packages` is unmangled
    assert any("reactpy" in package for package in result["packages"])

    # Check whether `js_modules` have been combined
    assert "/static/foo.js" in result["js_modules"]["main"]
    assert any("morphdom" in module for module in result["js_modules"]["main"])

    # Check whether `packages_cache` has been overridden
    assert result["packages_cache"] == "always"


def test_reactpy_pkg_string_prefers_packaged_wheel():
    wheel_file = _current_wheel_path()

    with (
        mock.patch(
            "reactpy.executors.pyscript.utils._source_checkout_exists",
            return_value=False,
        ),
        mock.patch(
            "reactpy.executors.pyscript.utils._find_current_reactpy_wheel",
            return_value=wheel_file,
        ),
        mock.patch(
            "reactpy.executors.pyscript.utils._rebuild_installed_reactpy_wheel"
        ) as rebuild_wheel,
    ):
        assert utils._reactpy_pkg_string() == (
            f"{REACTPY_PATH_PREFIX.current}static/wheels/{wheel_file.name}"
        )
        rebuild_wheel.assert_not_called()


def test_reactpy_pkg_string_rebuilds_source_checkout_when_wheel_is_stale():
    built_wheel = _current_wheel_path("dist")
    copied_wheel = _current_wheel_path("static", "wheels")

    with (
        mock.patch(
            "reactpy.executors.pyscript.utils._source_checkout_exists",
            return_value=True,
        ),
        mock.patch(
            "reactpy.executors.pyscript.utils._find_current_reactpy_wheel",
            return_value=copied_wheel,
        ),
        mock.patch(
            "reactpy.executors.pyscript.utils._wheel_is_stale_for_source",
            return_value=True,
        ),
        mock.patch(
            "reactpy.executors.pyscript.utils._build_reactpy_wheel_from_source",
            return_value=built_wheel,
        ) as build_wheel,
        mock.patch(
            "reactpy.executors.pyscript.utils._copy_reactpy_wheel_to_static_dir",
            return_value=copied_wheel,
        ) as copy_wheel,
    ):
        assert utils._reactpy_pkg_string() == (
            f"{REACTPY_PATH_PREFIX.current}static/wheels/{copied_wheel.name}"
        )
        build_wheel.assert_called_once_with()
        copy_wheel.assert_called_once_with(built_wheel)


def test_reactpy_pkg_string_reconstructs_installed_wheel_when_needed():
    wheel_file = _current_wheel_path()

    with (
        mock.patch(
            "reactpy.executors.pyscript.utils._source_checkout_exists",
            return_value=False,
        ),
        mock.patch(
            "reactpy.executors.pyscript.utils._find_current_reactpy_wheel",
            side_effect=[None, None],
        ),
        mock.patch(
            "reactpy.executors.pyscript.utils._rebuild_installed_reactpy_wheel",
            return_value=wheel_file,
        ) as rebuild_wheel,
    ):
        assert utils._reactpy_pkg_string() == (
            f"{REACTPY_PATH_PREFIX.current}static/wheels/{wheel_file.name}"
        )
        rebuild_wheel.assert_called_once_with()


def test_ensure_local_reactpy_wheel_keeps_current_source_checkout_wheel():
    wheel_file = _current_wheel_path()

    with (
        mock.patch(
            "reactpy.executors.pyscript.utils._source_checkout_exists",
            return_value=True,
        ),
        mock.patch(
            "reactpy.executors.pyscript.utils._find_current_reactpy_wheel",
            return_value=wheel_file,
        ),
        mock.patch(
            "reactpy.executors.pyscript.utils._wheel_is_stale_for_source",
            return_value=False,
        ),
        mock.patch(
            "reactpy.executors.pyscript.utils._build_reactpy_wheel_from_source"
        ) as build_wheel,
    ):
        assert utils._ensure_local_reactpy_wheel() == wheel_file

    build_wheel.assert_not_called()


def test_ensure_local_reactpy_wheel_replaces_stale_packaged_wheel_after_build():
    stale_wheel = _current_wheel_path("static", "wheels")
    built_wheel = _current_wheel_path("dist")
    copied_wheel = _current_wheel_path("static", "wheels")

    with (
        mock.patch(
            "reactpy.executors.pyscript.utils._source_checkout_exists",
            return_value=True,
        ),
        mock.patch(
            "reactpy.executors.pyscript.utils._find_current_reactpy_wheel",
            return_value=stale_wheel,
        ),
        mock.patch(
            "reactpy.executors.pyscript.utils._wheel_is_stale_for_source",
            return_value=True,
        ),
        mock.patch(
            "reactpy.executors.pyscript.utils._build_reactpy_wheel_from_source",
            return_value=built_wheel,
        ),
        mock.patch(
            "reactpy.executors.pyscript.utils._copy_reactpy_wheel_to_static_dir",
            return_value=copied_wheel,
        ) as copy_wheel,
    ):
        assert utils._ensure_local_reactpy_wheel() == copied_wheel

    copy_wheel.assert_called_once_with(built_wheel)


def test_ensure_local_reactpy_wheel_copies_built_wheel_when_packaged_copy_missing():
    stale_wheel = _current_wheel_path()
    built_wheel = _current_wheel_path("dist")
    copied_wheel = _current_wheel_path("static", "wheels")

    with (
        mock.patch(
            "reactpy.executors.pyscript.utils._source_checkout_exists",
            return_value=True,
        ),
        mock.patch(
            "reactpy.executors.pyscript.utils._find_current_reactpy_wheel",
            side_effect=[stale_wheel, None],
        ),
        mock.patch(
            "reactpy.executors.pyscript.utils._wheel_is_stale_for_source",
            return_value=True,
        ),
        mock.patch(
            "reactpy.executors.pyscript.utils._build_reactpy_wheel_from_source",
            return_value=built_wheel,
        ),
        mock.patch(
            "reactpy.executors.pyscript.utils._copy_reactpy_wheel_to_static_dir",
            return_value=copied_wheel,
        ) as copy_wheel,
    ):
        assert utils._ensure_local_reactpy_wheel() == copied_wheel
        copy_wheel.assert_called_once_with(built_wheel)


def test_ensure_local_reactpy_wheel_raises_when_source_build_fails():
    with (
        mock.patch(
            "reactpy.executors.pyscript.utils._source_checkout_exists",
            return_value=True,
        ),
        mock.patch(
            "reactpy.executors.pyscript.utils._find_current_reactpy_wheel",
            return_value=None,
        ),
        mock.patch(
            "reactpy.executors.pyscript.utils._build_reactpy_wheel_from_source",
            return_value=None,
        ),
    ):
        with pytest.raises(RuntimeError, match="could not build a local wheel"):
            utils._ensure_local_reactpy_wheel()


def test_ensure_local_reactpy_wheel_raises_when_installed_wheel_is_missing():
    with (
        mock.patch(
            "reactpy.executors.pyscript.utils._source_checkout_exists",
            return_value=False,
        ),
        mock.patch(
            "reactpy.executors.pyscript.utils._find_current_reactpy_wheel",
            return_value=None,
        ),
        mock.patch(
            "reactpy.executors.pyscript.utils._rebuild_installed_reactpy_wheel",
            return_value=None,
        ),
    ):
        with pytest.raises(RuntimeError, match="could not locate or reconstruct"):
            utils._ensure_local_reactpy_wheel()


def test_find_current_reactpy_wheel_returns_none_for_missing_directory(tmp_path):
    assert utils._find_current_reactpy_wheel(tmp_path / "missing") is None


def test_source_checkout_exists_uses_repo_root_pyproject(tmp_path, monkeypatch):
    package_file = tmp_path / "src" / "reactpy" / "__init__.py"
    _write_file(package_file, "__version__ = '0.0.0'\n")
    monkeypatch.setattr(utils.reactpy, "__file__", str(package_file))

    assert utils._reactpy_repo_root() == tmp_path
    assert utils._source_checkout_exists() is False

    _write_file(tmp_path / "pyproject.toml", "[project]\n")
    assert utils._source_checkout_exists() is True


def test_find_current_reactpy_wheel_selects_matching_local_version(tmp_path):
    wheel_dir = tmp_path / "wheels"
    wheel_dir.mkdir()
    expected = _write_file(
        wheel_dir / f"reactpy-{utils.reactpy.__version__}-py3-none-any.whl",
        "wheel-a",
    )
    _write_file(
        wheel_dir
        / f"reactpy-{utils.reactpy.__version__.replace('.', '_')}-py3-none-any.whl",
        "wheel-b",
    )
    _write_file(wheel_dir / "reactpy-0.0.1-py3-none-any.whl", "old-wheel")

    assert utils._find_current_reactpy_wheel(wheel_dir) == expected
    assert utils._wheel_matches_local_version(expected) is True
    assert (
        utils._wheel_matches_local_version(Path("other-1.0.0-py3-none-any.whl"))
        is False
    )
    assert utils._normalize_wheel_part("2_0.0-b11") == "2-0-0-b11"


def test_wheel_is_stale_for_source_when_pyproject_changes(tmp_path):
    wheel_file = _write_file(
        tmp_path / "dist" / _current_wheel_name(),
        "wheel",
        mtime=10,
    )
    _write_file(tmp_path / "pyproject.toml", "[project]\n", mtime=20)
    (tmp_path / "src" / "reactpy").mkdir(parents=True)

    with (
        mock.patch(
            "reactpy.executors.pyscript.utils._reactpy_repo_root",
            return_value=tmp_path,
        ),
        mock.patch(
            "reactpy.executors.pyscript.utils._packaged_reactpy_wheels_dir",
            return_value=tmp_path / "src" / "reactpy" / "static" / "wheels",
        ),
    ):
        assert utils._wheel_is_stale_for_source(wheel_file) is True


def test_wheel_is_stale_for_source_ignores_cache_and_packaged_wheels(tmp_path):
    repo_root = tmp_path
    source_dir = repo_root / "src" / "reactpy"
    packaged_wheels_dir = source_dir / "static" / "wheels"
    wheel_file = _write_file(
        repo_root / "dist" / _current_wheel_name(),
        "wheel",
        mtime=10,
    )

    _write_file(repo_root / "pyproject.toml", "[project]\n", mtime=5)
    _write_file(source_dir / "__pycache__" / "ignored.pyc", "cached", mtime=30)
    _write_file(packaged_wheels_dir / wheel_file.name, "packaged", mtime=40)
    _write_file(source_dir / "component.py", "print('fresh')\n", mtime=50)

    with (
        mock.patch(
            "reactpy.executors.pyscript.utils._reactpy_repo_root",
            return_value=repo_root,
        ),
        mock.patch(
            "reactpy.executors.pyscript.utils._packaged_reactpy_wheels_dir",
            return_value=packaged_wheels_dir,
        ),
    ):
        assert utils._wheel_is_stale_for_source(wheel_file) is True


def test_wheel_is_not_stale_when_only_ignored_or_older_files_exist(tmp_path):
    repo_root = tmp_path
    source_dir = repo_root / "src" / "reactpy"
    packaged_wheels_dir = source_dir / "static" / "wheels"
    wheel_file = _write_file(
        repo_root / "dist" / _current_wheel_name(),
        "wheel",
        mtime=100,
    )

    _write_file(repo_root / "pyproject.toml", "[project]\n", mtime=90)
    (source_dir / "nested").mkdir(parents=True)
    _write_file(source_dir / "__pycache__" / "ignored.pyc", "cached", mtime=200)
    _write_file(packaged_wheels_dir / wheel_file.name, "packaged", mtime=200)
    _write_file(source_dir / "component.py", "print('old')\n", mtime=90)

    with (
        mock.patch(
            "reactpy.executors.pyscript.utils._reactpy_repo_root",
            return_value=repo_root,
        ),
        mock.patch(
            "reactpy.executors.pyscript.utils._packaged_reactpy_wheels_dir",
            return_value=packaged_wheels_dir,
        ),
    ):
        assert utils._wheel_is_stale_for_source(wheel_file) is False


def test_build_reactpy_wheel_from_source_returns_none_without_hatch(tmp_path):
    with (
        mock.patch(
            "reactpy.executors.pyscript.utils._reactpy_repo_root",
            return_value=tmp_path,
        ),
        mock.patch(
            "reactpy.executors.pyscript.utils._hatch_build_command",
            return_value=None,
        ),
    ):
        assert utils._build_reactpy_wheel_from_source() is None


def test_build_reactpy_wheel_from_source_handles_subprocess_error(tmp_path):
    with assert_reactpy_did_log(
        match_message="Failed to invoke Hatch while building a local ReactPy wheel.",
        error_type=OSError,
    ):
        with (
            mock.patch(
                "reactpy.executors.pyscript.utils._reactpy_repo_root",
                return_value=tmp_path,
            ),
            mock.patch(
                "reactpy.executors.pyscript.utils._hatch_build_command",
                return_value=["hatch", "build", "-t", "wheel"],
            ),
            mock.patch(
                "reactpy.executors.pyscript.utils.subprocess.run",
                side_effect=OSError,
            ),
        ):
            assert utils._build_reactpy_wheel_from_source() is None


def test_build_reactpy_wheel_from_source_returns_none_on_failed_build(tmp_path):
    with (
        mock.patch(
            "reactpy.executors.pyscript.utils._reactpy_repo_root",
            return_value=tmp_path,
        ),
        mock.patch(
            "reactpy.executors.pyscript.utils._hatch_build_command",
            return_value=["hatch", "build", "-t", "wheel"],
        ),
        mock.patch(
            "reactpy.executors.pyscript.utils.subprocess.run",
            return_value=mock.Mock(returncode=1, stdout="stdout", stderr="stderr"),
        ),
    ):
        assert utils._build_reactpy_wheel_from_source() is None


def test_build_reactpy_wheel_from_source_returns_built_wheel(tmp_path, monkeypatch):
    built_wheel = tmp_path / "dist" / _current_wheel_name()
    observed = {}

    monkeypatch.setenv("HATCH_ENV_ACTIVE", "default")
    monkeypatch.setenv("UNCHANGED_ENV", "keep")

    def fake_run(command, capture_output, text, check, cwd, env):
        observed["command"] = command
        observed["cwd"] = cwd
        observed["env"] = env
        return mock.Mock(returncode=0, stdout="", stderr="")

    with (
        mock.patch(
            "reactpy.executors.pyscript.utils._reactpy_repo_root",
            return_value=tmp_path,
        ),
        mock.patch(
            "reactpy.executors.pyscript.utils._hatch_build_command",
            return_value=["hatch", "build", "-t", "wheel"],
        ),
        mock.patch(
            "reactpy.executors.pyscript.utils.subprocess.run",
            side_effect=fake_run,
        ),
        mock.patch(
            "reactpy.executors.pyscript.utils._find_current_reactpy_wheel",
            return_value=built_wheel,
        ),
    ):
        assert utils._build_reactpy_wheel_from_source() == built_wheel

    assert observed["command"] == ["hatch", "build", "-t", "wheel"]
    assert observed["cwd"] == tmp_path
    assert "HATCH_ENV_ACTIVE" not in observed["env"]
    assert observed["env"]["UNCHANGED_ENV"] == "keep"


def test_hatch_build_command_prefers_repo_virtualenv_binary(tmp_path):
    hatch_path = tmp_path / ".venv" / "Scripts" / "hatch.exe"
    _write_file(hatch_path, "")

    assert utils._hatch_build_command(tmp_path) == [
        str(hatch_path),
        "build",
        "-t",
        "wheel",
    ]


def test_hatch_build_command_uses_system_hatch_when_available(tmp_path):
    with (
        mock.patch(
            "reactpy.executors.pyscript.utils.shutil.which",
            return_value="/usr/bin/hatch",
        ),
        mock.patch(
            "reactpy.executors.pyscript.utils.importlib.util.find_spec"
        ) as find_spec,
    ):
        assert utils._hatch_build_command(tmp_path) == [
            "/usr/bin/hatch",
            "build",
            "-t",
            "wheel",
        ]
        find_spec.assert_not_called()


def test_hatch_build_command_uses_python_module_when_available(tmp_path):
    with (
        mock.patch("reactpy.executors.pyscript.utils.shutil.which", return_value=None),
        mock.patch(
            "reactpy.executors.pyscript.utils.importlib.util.find_spec",
            return_value=object(),
        ),
    ):
        assert utils._hatch_build_command(tmp_path) == [
            utils.sys.executable,
            "-m",
            "hatch",
            "build",
            "-t",
            "wheel",
        ]


def test_hatch_build_command_returns_none_when_hatch_is_unavailable(tmp_path):
    with (
        mock.patch("reactpy.executors.pyscript.utils.shutil.which", return_value=None),
        mock.patch(
            "reactpy.executors.pyscript.utils.importlib.util.find_spec",
            return_value=None,
        ),
    ):
        assert utils._hatch_build_command(tmp_path) is None


def test_copy_reactpy_wheel_to_static_dir_replaces_previous_wheels(tmp_path):
    source_wheel = _write_file(
        tmp_path / "dist" / _current_wheel_name(),
        "new wheel",
    )
    static_wheels_dir = tmp_path / "static" / "wheels"
    _write_file(static_wheels_dir / "reactpy-1.0.0-py3-none-any.whl", "old wheel")

    with mock.patch(
        "reactpy.executors.pyscript.utils._packaged_reactpy_wheels_dir",
        return_value=static_wheels_dir,
    ):
        static_wheel = utils._copy_reactpy_wheel_to_static_dir(source_wheel)

    assert static_wheel == static_wheels_dir / source_wheel.name
    assert static_wheel.read_text(encoding="utf-8") == "new wheel"
    assert not (static_wheels_dir / "reactpy-1.0.0-py3-none-any.whl").exists()


def test_copy_reactpy_wheel_to_static_dir_replaces_same_name_wheel(tmp_path):
    source_wheel = _write_file(
        tmp_path / "dist" / _current_wheel_name(),
        "new wheel",
    )
    static_wheels_dir = tmp_path / "static" / "wheels"
    _write_file(static_wheels_dir / source_wheel.name, "old wheel")

    with mock.patch(
        "reactpy.executors.pyscript.utils._packaged_reactpy_wheels_dir",
        return_value=static_wheels_dir,
    ):
        static_wheel = utils._copy_reactpy_wheel_to_static_dir(source_wheel)

    assert static_wheel == static_wheels_dir / source_wheel.name
    assert static_wheel.read_text(encoding="utf-8") == "new wheel"


def test_copy_reactpy_wheel_to_static_dir_returns_existing_static_wheel(tmp_path):
    static_wheels_dir = tmp_path / "static" / "wheels"
    source_wheel = _write_file(
        static_wheels_dir / _current_wheel_name(),
        "existing wheel",
    )

    with (
        mock.patch(
            "reactpy.executors.pyscript.utils._packaged_reactpy_wheels_dir",
            return_value=static_wheels_dir,
        ),
        mock.patch("reactpy.executors.pyscript.utils.shutil.copy2") as copy_wheel,
    ):
        static_wheel = utils._copy_reactpy_wheel_to_static_dir(source_wheel)

    assert static_wheel == source_wheel
    assert static_wheel.read_text(encoding="utf-8") == "existing wheel"
    copy_wheel.assert_not_called()
    assert not static_wheel.with_suffix(f"{static_wheel.suffix}.tmp").exists()


def test_wheel_archive_name_rejects_unsafe_paths_and_normalizes_relative_paths():
    assert utils._wheel_archive_name(Path("reactpy") / "module.py") == (
        "reactpy/module.py"
    )
    assert utils._wheel_archive_name(Path("..") / "bin" / "reactpy") is None
    assert utils._wheel_archive_name(Path.cwd() / "reactpy" / "module.py") is None


def test_rebuild_installed_reactpy_wheel_returns_none_when_distribution_missing():
    with assert_reactpy_did_log(
        match_message="Could not inspect the installed ReactPy distribution.",
        error_type=utils.metadata.PackageNotFoundError,
    ):
        with mock.patch(
            "reactpy.executors.pyscript.utils.metadata.distribution",
            side_effect=utils.metadata.PackageNotFoundError,
        ):
            assert utils._rebuild_installed_reactpy_wheel() is None


def test_rebuild_installed_reactpy_wheel_returns_none_without_files():
    distribution = mock.Mock(files=[])

    with mock.patch(
        "reactpy.executors.pyscript.utils.metadata.distribution",
        return_value=distribution,
    ):
        assert utils._rebuild_installed_reactpy_wheel() is None


def test_rebuild_installed_reactpy_wheel_recreates_distribution_wheel(tmp_path):
    dist_info_dir = Path(f"reactpy-{utils.reactpy.__version__}.dist-info")
    installed_root = tmp_path / "installed"
    static_wheels_dir = tmp_path / "static" / "wheels"
    wheel_metadata = dist_info_dir / "WHEEL"
    record_metadata = dist_info_dir / "RECORD"
    files = [
        Path("reactpy") / "module.py",
        wheel_metadata,
        record_metadata,
        Path("reactpy") / "missing.py",
    ]

    _write_file(installed_root / "reactpy" / "module.py", "print('hello')\n")
    _write_file(
        installed_root / wheel_metadata,
        "Wheel-Version: 1.0\nTag: py3-none-any\n",
    )
    _write_file(installed_root / record_metadata, "old-record\n")
    distribution = _FakeDistribution(installed_root, files)

    with (
        mock.patch(
            "reactpy.executors.pyscript.utils.metadata.distribution",
            return_value=distribution,
        ),
        mock.patch(
            "reactpy.executors.pyscript.utils._packaged_reactpy_wheels_dir",
            return_value=static_wheels_dir,
        ),
    ):
        wheel_path = utils._rebuild_installed_reactpy_wheel()

    assert wheel_path == static_wheels_dir / (
        f"reactpy-{utils.reactpy.__version__}-py3-none-any.whl"
    )

    with ZipFile(wheel_path) as wheel_zip:
        names = set(wheel_zip.namelist())
        assert "reactpy/module.py" in names
        assert wheel_metadata.as_posix() in names
        assert "reactpy/missing.py" not in names

        record_text = wheel_zip.read(record_metadata.as_posix()).decode("utf-8")

    assert "reactpy/module.py,sha256=" in record_text
    assert f"{record_metadata.as_posix()},," in record_text


def test_rebuild_installed_reactpy_wheel_skips_generated_script_entries(tmp_path):
    dist_info_dir = Path(f"reactpy-{utils.reactpy.__version__}.dist-info")
    installed_root = tmp_path / "venv" / "lib" / "python3.13" / "site-packages"
    static_wheels_dir = tmp_path / "static" / "wheels"
    wheel_metadata = dist_info_dir / "WHEEL"
    record_metadata = dist_info_dir / "RECORD"
    entry_points_metadata = dist_info_dir / "entry_points.txt"
    generated_script = Path("..") / ".." / ".." / "bin" / "reactpy"
    files = [
        Path("reactpy") / "module.py",
        wheel_metadata,
        record_metadata,
        entry_points_metadata,
        generated_script,
    ]

    _write_file(installed_root / "reactpy" / "module.py", "print('hello')\n")
    _write_file(
        installed_root / wheel_metadata,
        "Wheel-Version: 1.0\nTag: py3-none-any\n",
    )
    _write_file(installed_root / record_metadata, "old-record\n")
    _write_file(
        installed_root / entry_points_metadata,
        "[console_scripts]\nreactpy = reactpy._console.cli:entry_point\n",
    )
    _write_file(
        tmp_path / "venv" / "bin" / "reactpy",
        "#!/usr/bin/env python\n",
    )
    distribution = _FakeDistribution(installed_root, files)

    with (
        mock.patch(
            "reactpy.executors.pyscript.utils.metadata.distribution",
            return_value=distribution,
        ),
        mock.patch(
            "reactpy.executors.pyscript.utils._packaged_reactpy_wheels_dir",
            return_value=static_wheels_dir,
        ),
    ):
        wheel_path = utils._rebuild_installed_reactpy_wheel()

    assert wheel_path == static_wheels_dir / (
        f"reactpy-{utils.reactpy.__version__}-py3-none-any.whl"
    )

    with ZipFile(wheel_path) as wheel_zip:
        names = set(wheel_zip.namelist())
        assert entry_points_metadata.as_posix() in names
        assert generated_script.as_posix() not in names

        record_text = wheel_zip.read(record_metadata.as_posix()).decode("utf-8")

    assert generated_script.as_posix() not in record_text


def test_installed_wheel_helpers_use_defaults_when_metadata_is_missing(tmp_path):
    distribution = _FakeDistribution(tmp_path, [])
    files = [Path("reactpy") / "module.py"]

    assert utils._installed_wheel_tag(files, distribution) == "py3-none-any"
    assert utils._installed_wheel_record_name(files) == (
        f"reactpy-{utils.reactpy.__version__}.dist-info/RECORD"
    )


def test_record_helpers_generate_csv_rows():
    row = utils._record_row("reactpy/module.py", b"abc")

    assert row[0] == "reactpy/module.py"
    assert row[1].startswith("sha256=")
    assert row[2] == "3"
    assert utils._record_text([row, ("reactpy.dist-info/RECORD", "", "")]) == (
        f"{row[0]},{row[1]},{row[2]}\nreactpy.dist-info/RECORD,,\n"
    )
