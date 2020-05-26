import json
import shutil
import subprocess
from loguru import logger
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional, List, Union, Dict, Any, Sequence

from .utils import Spinner


STATIC_DIR = Path(__file__).parent / "static"

CORE_MODULES = STATIC_DIR / "core_modules"
NODE_MODULES = STATIC_DIR / "node_modules"
WEB_MODULES = STATIC_DIR / "web_modules"


def web_module(name: str) -> str:
    path = f"../{WEB_MODULES.name}/{name}.js"
    if not web_module_exists(name):
        raise ValueError(f"Module '{path}' does not exist.")
    return path


def web_module_path(name: str) -> Optional[Path]:
    return _find_module_os_path(WEB_MODULES, name)


def web_module_exists(name: str) -> bool:
    return web_module_path(name) is not None


def define_web_module(name: str, source: str) -> str:
    path = _create_web_module_os_path(name)
    with path.open("w+") as f:
        f.write(source)
    return web_module(name)


def delete_web_modules(names: Sequence[str], skip_missing: bool = False) -> None:
    paths = []
    for n in _to_list_of_str(names):
        p = web_module_path(n)
        if p is not None:
            paths.append(p)
        elif not skip_missing:
            raise ValueError(f"Module '{n}' does not exist.")
    for p in paths:
        _delete_os_paths(p)


def install(
    packages: Sequence[str], exports: Sequence[str] = (), force: bool = False
) -> None:
    package_list = _to_list_of_str(packages)
    export_list = _to_list_of_str(exports)

    for pkg in package_list:
        at_count = pkg.count("@")
        if pkg.startswith("@") and at_count == 1:
            export_list.append(pkg)
        else:
            # this works even if there are no @ symbols
            export_list.append(pkg.rsplit("@", 1)[0])

    if force:
        for exp in export_list:
            delete_web_modules(exp, skip_missing=True)

    pkg = _package_json()
    pkg["snowpack"]["webDependencies"].extend(export_list)

    with TemporaryDirectory() as tempdir:
        tempdir_path = Path(tempdir)

        if NODE_MODULES.exists():
            shutil.copytree(
                NODE_MODULES, tempdir_path / NODE_MODULES.name, symlinks=True
            )

        with (tempdir_path / "package.json").open("w+") as f:
            json.dump(pkg, f)

        with Spinner(f"Installing: {', '.join(package_list)}"):
            _run_subprocess(["npm", "install"], tempdir)
            _run_subprocess(["npm", "install"] + package_list, tempdir)
            _run_subprocess(["npm", "run", "snowpack"], tempdir)


def restore() -> None:
    _delete_os_paths(WEB_MODULES, NODE_MODULES)
    _run_subprocess(["npm", "install"], STATIC_DIR)
    _run_subprocess(["npm", "run", "snowpack"], STATIC_DIR)


def _package_json() -> Dict[str, Any]:
    with (STATIC_DIR / "package.json").open("r") as f:
        dependencies = json.load(f)["dependencies"]

    return {
        "dependencies": dependencies,
        "scripts": {"snowpack": "./node_modules/.bin/snowpack"},
        "devDependencies": {"snowpack": "^1.6.0"},
        "snowpack": {
            "installOptions": {
                "dest": str(WEB_MODULES),
                "include": str(CORE_MODULES / "**" / "*.js"),
            },
            "webDependencies": [],
        },
    }


def _run_subprocess(args: List[str], cwd: Union[str, Path]) -> None:
    try:
        subprocess.run(
            args, cwd=cwd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
    except subprocess.CalledProcessError as error:
        if error.stderr is not None:
            logger.error(error.stderr.decode())
        raise
    return None


def _find_module_os_path(path: Path, name: str) -> Optional[Path]:
    for name_part in name.split("/"):
        if not path.is_dir():
            return None
        path /= name_part
    full_path = path.with_suffix(".js")
    if not full_path.is_file():
        return None
    return full_path


def _create_web_module_os_path(name: str) -> Path:
    path = WEB_MODULES
    for n in name.split("/"):
        if not path.exists():
            path.mkdir()
        path /= n
    return path.with_suffix(".js")


def _delete_os_paths(*paths: Path) -> None:
    for p in paths:
        if p.is_file():
            p.unlink()
        elif p.is_dir():
            shutil.rmtree(p)


def _to_list_of_str(value: Sequence[str]) -> List[str]:
    return [value] if isinstance(value, str) else list(value)
