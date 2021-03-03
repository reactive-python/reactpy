import json
import shutil
import subprocess
from logging import getLogger
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List, Sequence, Set, Union

from .utils import (
    find_js_module_exports_in_source,
    get_package_name,
    open_modifiable_json,
)

logger = getLogger(__name__)

APP_DIR = Path(__file__).parent / "app"
BUILD_DIR = APP_DIR / "build"
WEB_MODULES_DIR = BUILD_DIR / "web_modules"


def web_module_exports(package_name: str) -> List[str]:
    web_module_path(package_name, must_exist=True)
    return find_js_module_exports_in_source(
        web_module_path(package_name).read_text(encoding="utf-8")
    )


def web_module_url(package_name: str) -> str:
    web_module_path(package_name, must_exist=True)
    return f"./{package_name}.js"


def web_module_exists(package_name: str) -> bool:
    return web_module_path(package_name).exists()


def web_module_names() -> Set[str]:
    names = []
    for pth in WEB_MODULES_DIR.glob("**/*.js"):
        rel_pth = pth.relative_to(WEB_MODULES_DIR)
        if Path("common") in rel_pth.parents:
            continue
        module_path = str(rel_pth.as_posix())
        if module_path.endswith(".js"):
            module_path = module_path[:-3]
        names.append(module_path)
    return set(names)


def add_web_module(package_name: str, source: Union[Path, str]) -> str:
    source = Path(source)
    if not source.exists():
        raise FileNotFoundError(f"Package source file does not exist: {str(source)!r}")
    target = web_module_path(package_name)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.symlink_to(source.absolute())
    return web_module_url(package_name)


def web_module_path(package_name: str, must_exist: bool = False) -> Path:
    path = WEB_MODULES_DIR.joinpath(*(package_name + ".js").split("/"))
    if must_exist and not path.exists():
        raise ValueError(
            f"Web module {package_name!r} does not exist at path {str(path)!r}"
        )
    return path


def restore() -> None:
    build([], clean_build=True)


def build(packages_to_install: Sequence[str], clean_build: bool = False) -> None:
    packages_to_install = list(packages_to_install)

    with TemporaryDirectory() as tempdir:
        tempdir_path = Path(tempdir)
        temp_app_dir = tempdir_path / "app"
        temp_build_dir = temp_app_dir / "build"
        package_json_path = temp_app_dir / "package.json"

        # copy over the whole APP_DIR directory into the temp one
        shutil.copytree(APP_DIR, temp_app_dir, symlinks=True)

        package_names_to_install = {get_package_name(p) for p in packages_to_install}

        # make sure we don't delete anything we've already installed
        built_package_json_path = temp_build_dir / "package.json"
        if not clean_build and built_package_json_path.exists():
            built_package_json = json.loads(built_package_json_path.read_text())
            for dep_name, dep_ver in built_package_json.get("dependencies", {}).items():
                if dep_name not in package_names_to_install:
                    packages_to_install.append(f"{dep_name}@{dep_ver}")
                    package_names_to_install.add(dep_name)

        with open_modifiable_json(package_json_path) as package_json:
            snowpack_config = package_json.setdefault("snowpack", {})

            snowpack_install = snowpack_config.setdefault("install", [])
            snowpack_install.extend(package_names_to_install)

            snowpack_build = snowpack_config.setdefault("buildOptions", {})
            snowpack_build["clean"] = clean_build

        logger.info(f"Installing {packages_to_install or 'packages'} ...")
        _npm_install(packages_to_install, temp_app_dir)
        logger.info("Installed successfully ✅")

        logger.debug(f"package.json: {package_json_path.read_text()}")

        logger.info("Building client ...")
        _npm_run_build(temp_app_dir)
        logger.info("Client built successfully ✅")

        if BUILD_DIR.exists():
            shutil.rmtree(BUILD_DIR)

        shutil.copytree(temp_build_dir, BUILD_DIR, symlinks=True)

    not_discovered = package_names_to_install.difference(web_module_names())
    if not_discovered:
        raise RuntimeError(  # pragma: no cover
            f"Successfuly installed {list(package_names_to_install)} but "
            f"failed to discover {list(not_discovered)} post-install."
        )


def _npm_install(packages: List[str], cwd: Path) -> None:
    _run_subprocess(["npm", "install"] + packages, cwd)


def _npm_run_build(cwd: Path) -> None:
    _run_subprocess(["npm", "run", "build"], cwd)


def _run_subprocess(args: List[str], cwd: Path) -> None:
    cmd, *args = args
    which_cmd = shutil.which(cmd)
    if which_cmd is None:
        raise RuntimeError(  # pragma: no cover
            f"Failed to run command - {cmd!r} is not installed."
        )
    try:
        subprocess.run(
            [which_cmd] + args,
            cwd=cwd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as error:  # pragma: no cover
        raise subprocess.SubprocessError(error.stderr.decode()) from error
    return None
