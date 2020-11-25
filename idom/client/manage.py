import shutil
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional, Iterable, Sequence, List

from .build_config import (
    BuildConfig,
    BuildConfigItem,
    find_python_packages_build_config_items,
)
from .utils import open_modifiable_json

from idom.cli import console


APP_DIR = Path(__file__).parent / "app"
BUILD_DIR = APP_DIR / "build"


def build_config() -> BuildConfig:
    return BuildConfig(BUILD_DIR)


def find_path(url_path: str) -> Optional[Path]:
    url_path = url_path.strip("/")

    builtin_path = BUILD_DIR.joinpath(*url_path.split("/"))
    if builtin_path.exists():
        return builtin_path
    else:
        return None


def web_module_url(source_name: str, package_name: str) -> Optional[str]:
    config = build_config().configs.get(source_name)
    if config is None:
        return None
    if package_name not in config.js_dependency_aliases:
        return None
    alias = config.js_dependency_aliases[package_name]
    if find_path(f"web_modules/{alias}.js") is None:
        return None
    # need to go back a level since the JS that import this is in `core_components`
    return f"../web_modules/{alias}.js"


def build(
    config_items: Optional[Iterable[BuildConfigItem]] = None,
    output_dir: Path = BUILD_DIR,
) -> None:
    config = build_config()

    with config.transaction():
        if config_items is not None:
            config.update_config_items(config_items)

        with console.spinner("Discovering dependencies"):
            configs, errors = find_python_packages_build_config_items()
            for e in errors:
                console.echo(f"{e} because {e.__cause__}", color="red")
            config.update_config_items(configs)

    with TemporaryDirectory() as tempdir:
        tempdir_path = Path(tempdir)
        temp_app_dir = tempdir_path / "app"
        temp_build_dir = temp_app_dir / "build"
        package_json_path = temp_app_dir / "package.json"

        # copy over the whole APP_DIR directory into the temp one
        shutil.copytree(APP_DIR, temp_app_dir, symlinks=True)

        packages_to_install = config.all_aliased_js_dependencies()

        with open_modifiable_json(package_json_path) as package_json:
            snowpack_config = package_json.setdefault("snowpack", {})
            snowpack_config.setdefault("install", []).extend(
                config.all_js_dependency_aliases()
            )

        with console.spinner(
            f"Installing {len(packages_to_install)} dependencies"
            if packages_to_install
            else "Installing dependencies"
        ):
            _npm_install(packages_to_install, temp_app_dir)

        with console.spinner("Building client"):
            _npm_run_build(temp_app_dir)

        if output_dir.exists():
            shutil.rmtree(output_dir)

        shutil.copytree(temp_build_dir, output_dir, symlinks=True)


def restore() -> None:
    with console.spinner("Restoring"):
        shutil.rmtree(BUILD_DIR)
        _run_subprocess(["npm", "install"], APP_DIR)
        _run_subprocess(["npm", "run", "build"], APP_DIR)


def _npm_install(packages: Sequence[str], cwd: Path) -> None:
    _run_subprocess(["npm", "install"] + packages, cwd)


def _npm_run_build(cwd: Path):
    _run_subprocess(["npm", "run", "build"], cwd)


def _run_subprocess(args: List[str], cwd: Path) -> None:
    try:
        subprocess.run(
            args, cwd=cwd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
    except subprocess.CalledProcessError as error:
        raise subprocess.SubprocessError(error.stderr.decode()) from error
    return None
