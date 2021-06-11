import json
import logging
import re
import shutil
from os.path import getmtime
from pathlib import Path
from typing import Dict, Set, Tuple, cast

from idom.config import IDOM_CLIENT_BUILD_DIR


logger = logging.getLogger(__name__)

HERE = Path(__file__).parent
APP_DIR = HERE / "app"
BACKUP_BUILD_DIR = APP_DIR / "build"

# the path relative to the build that contains import sources
IDOM_CLIENT_IMPORT_SOURCE_INFIX = "_snowpack/pkg"


def _run_build_dir_init_only_once() -> None:  # pragma: no cover
    """Initialize the runtime build directory - this should only be called once"""
    if not IDOM_CLIENT_BUILD_DIR.current.exists():
        logger.debug("creating new runtime build directory")
        IDOM_CLIENT_BUILD_DIR.current.parent.mkdir(parents=True, exist_ok=True)
        # populate the runtime build directory if it doesn't exist
        shutil.copytree(BACKUP_BUILD_DIR, IDOM_CLIENT_BUILD_DIR.current, symlinks=True)
    elif getmtime(BACKUP_BUILD_DIR) > getmtime(IDOM_CLIENT_BUILD_DIR.current):
        logger.debug("updating runtime build directory because it is out of date")
        # delete the existing runtime build because it's out of date
        shutil.rmtree(IDOM_CLIENT_BUILD_DIR.current)
        # replace it with the newer backup build (presumable from a fresh install)
        shutil.copytree(BACKUP_BUILD_DIR, IDOM_CLIENT_BUILD_DIR.current, symlinks=True)
    else:
        logger.debug("runtime build directory is up to date")


_run_build_dir_init_only_once()  # this is only ever called once at runtime!


def get_user_packages_file(app_dir: Path) -> Path:
    return app_dir / "packages" / "idom-app-react" / "src" / "user-packages.js"


def restore_build_dir_from_backup() -> None:
    target = IDOM_CLIENT_BUILD_DIR.current
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(BACKUP_BUILD_DIR, target, symlinks=True)


def replace_build_dir(source: Path) -> None:
    target = IDOM_CLIENT_BUILD_DIR.current
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target, symlinks=True)


def get_package_name(pkg: str) -> str:
    return split_package_name_and_version(pkg)[0]


def split_package_name_and_version(pkg: str) -> Tuple[str, str]:
    at_count = pkg.count("@")
    if pkg.startswith("@"):
        if at_count == 1:
            return pkg, ""
        else:
            name, version = pkg[1:].split("@", 1)
            return ("@" + name), version
    elif at_count:
        name, version = pkg.split("@", 1)
        return name, version
    else:
        return pkg, ""


def build_dependencies() -> Dict[str, str]:
    package_json = IDOM_CLIENT_BUILD_DIR.current / "package.json"
    return cast(Dict[str, str], json.loads(package_json.read_text())["dependencies"])


_JS_MODULE_EXPORT_PATTERN = re.compile(
    r";?\s*export\s*{([0-9a-zA-Z_$\s,]*)}\s*;", re.MULTILINE
)
_JS_VAR = r"[a-zA-Z_$][0-9a-zA-Z_$]*"
_JS_MODULE_EXPORT_NAME_PATTERN = re.compile(
    fr";?\s*export\s+({_JS_VAR})\s+{_JS_VAR}\s*;", re.MULTILINE
)
_JS_MODULE_EXPORT_FUNC_PATTERN = re.compile(
    fr";?\s*export\s+function\s+({_JS_VAR})\s*\(.*?", re.MULTILINE
)


def find_js_module_exports_in_source(content: str) -> Set[str]:
    names: Set[str] = set()
    for match in _JS_MODULE_EXPORT_PATTERN.findall(content):
        for export in match.split(","):
            export_parts = export.split(" as ", 1)
            names.add(export_parts[-1].strip())
    names.update(_JS_MODULE_EXPORT_FUNC_PATTERN.findall(content))
    names.update(_JS_MODULE_EXPORT_NAME_PATTERN.findall(content))
    return names
