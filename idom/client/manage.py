import shutil
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional, Iterable, Sequence, List

from .build_config import (
    BuildConfigFile,
    BuildConfigItem,
    find_python_packages_build_config_items,
)
from .utils import open_modifiable_json, split_package_name_and_version

from idom.cli import console


APP_DIR = Path(__file__).parent / "app"
BUILD_DIR = APP_DIR / "build"
BUILD_CONFIG_FILE = BuildConfigFile(BUILD_DIR)


def find_path(url_path: str) -> Optional[Path]:
    url_path = url_path.strip("/")

    builtin_path = BUILD_DIR.joinpath(*url_path.split("/"))
    if builtin_path.exists():
        return builtin_path
    else:
        return None


def web_module_url(source_name: str, package_name: str) -> str:
    config = BUILD_CONFIG_FILE.configs.get(source_name)
    if config is None:
        return None
    alias = config.get_js_dependency_alias(package_name)
    if find_path(f"web_modules/{alias}.js") is None:
        return None
    # need to go back a level since the JS that import this is in `core_components`
    return f"../web_modules/{alias}.js"


def build(
    configs: Optional[Iterable[BuildConfigItem]] = None,
    output_dir: Path = BUILD_DIR,
) -> None:
    with BUILD_CONFIG_FILE.transaction():
        if configs is not None:
            BUILD_CONFIG_FILE.add(configs, ignore_existing=True)

        with console.spinner("Discovering dependencies"):
            BUILD_CONFIG_FILE.add(
                find_python_packages_build_config_items(), ignore_existing=True
            )

        with TemporaryDirectory() as tempdir:
            tempdir_path = Path(tempdir)
            temp_app_dir = tempdir_path / "app"
            temp_build_dir = temp_app_dir / "build"
            package_json_path = temp_app_dir / "package.json"

            # copy over the whole APP_DIR directory into the temp one
            shutil.copytree(APP_DIR, temp_app_dir, symlinks=True)

            packages_to_install = [
                dep
                for conf in BUILD_CONFIG_FILE.configs.values()
                for dep in conf.aliased_js_dependencies()
            ]

            with open_modifiable_json(package_json_path) as package_json:
                snowpack_config = package_json.setdefault("snowpack", {})
                snowpack_config.setdefault("install", []).extend(
                    [
                        split_package_name_and_version(dep)[0]
                        for dep in packages_to_install
                    ]
                )

            with console.spinner(f"Installing {len(packages_to_install)} dependencies"):
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
