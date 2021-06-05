"""
Client Manager
==============
"""

import shutil
import subprocess
import sys
from logging import getLogger
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Dict, Iterable, List, Sequence, Set, Union

from idom.config import IDOM_CLIENT_BUILD_DIR

from . import _private


logger = getLogger(__name__)


def web_modules_dir() -> Path:
    """The directory containing all web modules

    .. warning::

        No assumptions should be made about the exact structure of this directory!
    """
    return IDOM_CLIENT_BUILD_DIR.current / "_snowpack" / "pkg"


def web_module_path(package_name: str, must_exist: bool = False) -> Path:
    """Get the :class:`Path` to a web module's source"""
    path = web_modules_dir().joinpath(*(package_name + ".js").split("/"))
    if must_exist and not path.exists():
        raise ValueError(
            f"Web module {package_name!r} does not exist at path {str(path)!r}"
        )
    return path


def web_module_exports(package_name: str) -> Set[str]:
    """Get a list of names this module exports"""
    web_module_path(package_name, must_exist=True)
    return _private.find_js_module_exports_in_source(
        web_module_path(package_name).read_text(encoding="utf-8")
    )


def web_module_exists(package_name: str) -> bool:
    """Whether a web module with a given name exists"""
    return web_module_path(package_name).exists()


def web_module_names() -> Set[str]:
    """Get the names of all installed web modules"""
    names = []
    web_mod_dir = web_modules_dir()
    for pth in web_mod_dir.glob("**/*.js"):
        rel_pth = pth.relative_to(web_mod_dir)
        if Path("common") in rel_pth.parents:
            continue
        module_path = str(rel_pth.as_posix())
        if module_path.endswith(".js"):
            module_path = module_path[:-3]
        names.append(module_path)
    return set(names)


def add_web_module(
    package_name: str,
    source: Union[Path, str],
) -> None:
    """Add a web module from source"""
    resolved_source = Path(source).resolve()
    if not resolved_source.exists():
        raise FileNotFoundError(f"Package source file does not exist: {str(source)!r}")
    target = web_module_path(package_name)
    if target.resolve() == resolved_source:
        return None  # already added
    target.parent.mkdir(parents=True, exist_ok=True)
    # this will raise an error if already exists
    target.symlink_to(resolved_source)


def remove_web_module(package_name: str, must_exist: bool = False) -> None:
    """Remove a web module"""
    web_module_path(package_name, must_exist).unlink()


def restore() -> None:
    _private.restore_build_dir_from_backup()


def build(
    packages: Sequence[str],
    clean_build: bool = True,
    skip_if_already_installed: bool = True,
) -> None:
    """Build the client"""
    package_specifiers_to_install = list(packages)
    del packages  # delete since we just renamed it

    packages_to_install = _parse_package_specs(package_specifiers_to_install)
    installed_packages = _private.build_dependencies()

    if clean_build:
        all_packages = packages_to_install
    else:
        if skip_if_already_installed:
            for pkg_name, pkg_ver in packages_to_install.items():
                if pkg_name not in installed_packages or (
                    pkg_ver and installed_packages[pkg_name] != pkg_ver
                ):
                    break
            else:
                logger.info(f"Already installed {package_specifiers_to_install}")
                logger.info("Build skipped ✅")
                return None
        all_packages = {**installed_packages, **packages_to_install}

    all_package_specifiers = [f"{p}@{v}" if v else p for p, v in all_packages.items()]

    with TemporaryDirectory() as tempdir:
        tempdir_path = Path(tempdir)
        temp_app_dir = tempdir_path / "app"
        temp_build_dir = temp_app_dir / "build"
        package_json_path = temp_app_dir / "package.json"

        # copy over the whole APP_DIR directory into the temp one
        shutil.copytree(_private.APP_DIR, temp_app_dir, symlinks=True)

        _write_user_packages_file(temp_app_dir, list(all_packages))

        logger.info("Installing dependencies...")
        _npm_install(all_package_specifiers, temp_app_dir)
        logger.info("Installed successfully ✅")

        logger.debug(f"package.json: {package_json_path.read_text()}")

        logger.info("Building client ...")
        _npm_run_build(temp_app_dir)
        logger.info("Client built successfully ✅")

        _private.replace_build_dir(temp_build_dir)

    not_discovered = set(all_packages).difference(web_module_names())
    if not_discovered:
        raise RuntimeError(  # pragma: no cover
            f"Successfuly installed {list(all_packages)} but "
            f"failed to discover {list(not_discovered)} post-install."
        )


if sys.platform == "win32" and sys.version_info[:2] == (3, 7):  # pragma: no cover

    def build(
        packages: Sequence[str],
        clean_build: bool = True,
        skip_if_already_installed: bool = True,
    ) -> None:
        msg = (
            "This feature is not available due to a bug in Python<3.8 on Windows - for "
            "more information see: https://bugs.python.org/issue31226"
        )
        try:
            import pytest
        except ImportError:
            raise NotImplementedError(msg)
        else:
            pytest.xfail(msg)


def _parse_package_specs(package_strings: Sequence[str]) -> Dict[str, str]:
    return {
        dep: ver
        for dep, ver in map(_private.split_package_name_and_version, package_strings)
    }


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


def _write_user_packages_file(app_dir: Path, packages: Iterable[str]) -> None:
    _private.get_user_packages_file(app_dir).write_text(
        _USER_PACKAGES_FILE_TEMPLATE.format(
            imports=",".join(f'"{pkg}":import({pkg!r})' for pkg in packages)
        )
    )


_USER_PACKAGES_FILE_TEMPLATE = """// THIS FILE WAS GENERATED BY IDOM - DO NOT MODIFY
export default {{{imports}}};
"""
