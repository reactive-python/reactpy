import shutil
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional, List, Dict, Sequence

from .sh import spinner
from .build_config import (
    BuildConfig,
    save_build_configs,
    load_build_configs,
    find_python_packages_build_configs,
)
from .utils import open_modifiable_json, split_package_name_and_version


APP_DIR = Path(__file__).parent / "app"
BUILD_DIR = APP_DIR / "build"
WEB_MODULES_DIR = BUILD_DIR / "web_modules"


STATIC_SHIMS: Dict[str, Path] = {}
_BUILD_CONFIGS = load_build_configs(BUILD_DIR)


def build_configs() -> Dict[str, BuildConfig]:
    return _BUILD_CONFIGS.copy()


def find_path(url_path: str) -> Optional[Path]:
    url_path = url_path.strip("/")

    builtin_path = BUILD_DIR.joinpath(*url_path.split("/"))
    if builtin_path.exists():
        return builtin_path

    return STATIC_SHIMS.get(url_path)


def web_module_url(source_name: str, package_name: str) -> str:
    config = build_configs().get(source_name)
    if config is None:
        return None
    alias = config.get_js_dependency_alias(package_name)
    if find_path(f"web_modules/{alias}.js") is None:
        return None
    # need to go back a level since the JS that import this is in `core_components`
    return f"../web_modules/{alias}.js"


def build(*extra_configs: Optional[BuildConfig], output_dir: Path = BUILD_DIR) -> None:
    with spinner("Discovering dependencies"):
        build_configs = find_python_packages_build_configs()
        for conf in extra_configs:
            if conf is not None:
                build_configs[conf.source_name] = conf

    with TemporaryDirectory() as tempdir:
        tempdir_path = Path(tempdir)
        temp_app_dir = tempdir_path / "app"
        temp_build_dir = temp_app_dir / "build"
        package_json_path = temp_app_dir / "package.json"

        # copy over the whole APP_DIR directory into the temp one
        shutil.copytree(APP_DIR, temp_app_dir, symlinks=True)

        packages_to_install = [
            dep
            for conf in build_configs.values()
            for dep in conf.aliased_js_dependencies()
        ]

        with open_modifiable_json(package_json_path) as package_json:
            snowpack_config = package_json.setdefault("snowpack", {})
            snowpack_config.setdefault("install", []).extend(
                [split_package_name_and_version(dep)[0] for dep in packages_to_install]
            )

        with spinner(f"Installing {len(packages_to_install)} dependencies"):
            _npm_install(packages_to_install, temp_app_dir)

        with spinner("Building client"):
            _npm_run_build(temp_app_dir)

        if output_dir.exists():
            shutil.rmtree(output_dir)

        shutil.copytree(temp_build_dir, output_dir, symlinks=True)
        save_build_configs(output_dir, build_configs)


def restore() -> None:
    with spinner("Restoring"):
        shutil.rmtree(BUILD_DIR)
        _run_subprocess(["npm", "install"], APP_DIR)
        _run_subprocess(["npm", "run", "build"], APP_DIR)
        STATIC_SHIMS.clear()


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
