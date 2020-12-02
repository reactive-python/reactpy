import shutil
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional, Iterable, Sequence, List, Tuple

from .build_config import (
    BuildConfig,
    ConfigItem,
    find_python_packages_build_config_items,
)
from .utils import open_modifiable_json, find_js_module_exports_in_source

from idom.cli import console


APP_DIR = Path(__file__).parent / "app"
BUILD_DIR = APP_DIR / "build"
_BUILD_CONFIG: Optional[BuildConfig] = None


class WebModuleError(Exception):
    """Related to the use of javascript web modules"""


def build_config() -> BuildConfig:
    global _BUILD_CONFIG
    if _BUILD_CONFIG is None:
        _BUILD_CONFIG = BuildConfig(BUILD_DIR)
    return _BUILD_CONFIG


def web_module_exports(source_name: str, package_name: str) -> List[str]:
    _, module_file = _get_web_module_name_and_file_path(source_name, package_name)
    with module_file.open() as f:
        return find_js_module_exports_in_source(f.read())


def web_module_url(source_name: str, package_name: str) -> Optional[str]:
    name, _ = _get_web_module_name_and_file_path(source_name, package_name)
    # need to go back a level since the JS that imports this is in `core_components`
    return f"../web_modules/{name}.js"


def web_module_exists(source_name: str, package_name: str) -> bool:
    try:
        _get_web_module_name_and_file_path(source_name, package_name)
    except WebModuleError:
        return False
    else:
        return True


def build(config_items: Iterable[ConfigItem] = ()) -> None:
    config = build_config()
    with console.spinner("Discovering dependencies"):
        py_pkg_configs, errors = find_python_packages_build_config_items()
    for e in errors:  # pragma: no cover
        console.echo(f"{e} because {e.__cause__}", message_color="red")
    config.update(py_pkg_configs + list(config_items))

    with TemporaryDirectory() as tempdir:
        tempdir_path = Path(tempdir)
        temp_app_dir = tempdir_path / "app"
        temp_build_dir = temp_app_dir / "build"
        package_json_path = temp_app_dir / "package.json"

        # copy over the whole APP_DIR directory into the temp one
        shutil.copytree(APP_DIR, temp_app_dir, symlinks=True)

        packages_to_install = config.all_js_dependencies()

        with open_modifiable_json(package_json_path) as package_json:
            snowpack_config = package_json.setdefault("snowpack", {})
            snowpack_install = snowpack_config.setdefault("install", [])
            snowpack_install.extend(config.all_js_dependency_names())

        with console.spinner(
            f"Installing {len(packages_to_install)} dependencies"
            if packages_to_install
            else "Installing dependencies"
        ):
            _npm_install(packages_to_install, temp_app_dir)

        with console.spinner("Building client"):
            _npm_run_build(temp_app_dir)

        if BUILD_DIR.exists():
            shutil.rmtree(BUILD_DIR)

        shutil.copytree(temp_build_dir, BUILD_DIR, symlinks=True)

    config.save()


def restore() -> None:
    with console.spinner("Restoring"):
        if BUILD_DIR.exists():
            shutil.rmtree(BUILD_DIR)
        _run_subprocess(["npm", "install"], APP_DIR)
        _run_subprocess(["npm", "run", "build"], APP_DIR)


def _get_web_module_name_and_file_path(
    source_name: str, package_name: str
) -> Tuple[str, Path]:
    pkg_name = build_config().resolve_js_dependency_name(source_name, package_name)
    if pkg_name is None:
        raise WebModuleError(
            f"Package {package_name!r} is not declared as a dependency of {source_name!r}"
        )
    builtin_path = BUILD_DIR.joinpath("web_modules", *f"{pkg_name}.js".split("/"))
    if not builtin_path.exists():
        raise WebModuleError(
            f"Dependency {package_name!r} of {source_name!r} was not installed"
        )
    return pkg_name, builtin_path


def _npm_install(packages: Sequence[str], cwd: Path) -> None:
    _run_subprocess(["npm", "install"] + packages, cwd)


def _npm_run_build(cwd: Path) -> None:
    _run_subprocess(["npm", "run", "build"], cwd)


def _run_subprocess(args: List[str], cwd: Path) -> None:
    try:
        subprocess.run(
            args, cwd=cwd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
    except subprocess.CalledProcessError as error:
        raise subprocess.SubprocessError(error.stderr.decode()) from error
    return None
