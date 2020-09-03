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

STATIC_SHIMS: Dict[str, Path] = {}


def find_path(url_path: str) -> Optional[Path]:
    url_path = url_path.strip("/")

    builtin_path = STATIC_DIR.joinpath(*url_path.split("/"))
    if builtin_path.exists():
        return builtin_path

    return STATIC_SHIMS.get(url_path)


def web_module_path(name: str) -> Optional[Path]:
    return find_path(f"web_modules/{name}.js")


def web_module_url(name: str) -> str:
    path = f"../{WEB_MODULES.name}/{name}.js"
    if not web_module_exists(name):
        raise ValueError(f"Module '{path}' does not exist.")
    return path


def web_module_exists(name: str) -> bool:
    return find_path(f"web_modules/{name}.js") is not None


def register_web_module(name: str, source: Union[str, Path]) -> str:
    source_path = source if isinstance(source, Path) else Path(source)
    if web_module_exists(name):
        raise ValueError(f"Web module {name} already exists")
    if not source_path.is_file():
        raise ValueError(f"Web modules source {source} does not exist or is not a file")
    STATIC_SHIMS[f"web_modules/{name}.js"] = source_path
    return web_module_url(name)


def delete_web_modules(names: Sequence[str], skip_missing: bool = False) -> None:
    paths = []
    for name in _to_list_of_str(names):
        exists = False

        dir_name = f"web_modules/{name}"
        js_name = f"web_modules/{name}.js"
        path = find_path(dir_name)
        js_path = find_path(js_name)

        if path is not None:
            paths.append(path)
            exists = True

        if js_name in STATIC_SHIMS:
            del STATIC_SHIMS[js_name]
            exists = True
        elif js_path is not None:
            paths.append(js_path)
            exists = True

        if not exists and not skip_missing:
            raise ValueError(f"Module '{name}' does not exist.")

    for p in paths:
        _delete_os_paths(p)


def installed() -> List[str]:
    names: List[str] = []
    for path in WEB_MODULES.rglob("*"):
        if path.is_file() and path.suffix == ".js":
            rel_path = path.relative_to(WEB_MODULES)
            names.append(str(rel_path.with_suffix("")))
    return list(sorted(names))


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

    package_json = _package_json()
    package_json["snowpack"]["webDependencies"].extend(export_list)

    with TemporaryDirectory() as tempdir:
        tempdir_path = Path(tempdir)

        if NODE_MODULES.exists():
            shutil.copytree(
                NODE_MODULES, tempdir_path / NODE_MODULES.name, symlinks=True
            )

        with (tempdir_path / "package.json").open("w+") as f:
            json.dump(package_json, f)

        with Spinner(f"Installing: {', '.join(package_list)}"):
            _run_subprocess(["npm", "install"], tempdir)
            _run_subprocess(["npm", "install"] + package_list, tempdir)
            _run_subprocess(["npm", "run", "snowpack"], tempdir)


def restore() -> None:
    with Spinner("Restoring"):
        _delete_os_paths(WEB_MODULES, NODE_MODULES)
        _run_subprocess(["npm", "install"], STATIC_DIR)
        _run_subprocess(["npm", "run", "snowpack"], STATIC_DIR)
    STATIC_SHIMS.clear()


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


def _delete_os_paths(*paths: Path) -> None:
    for p in paths:
        if p.is_file():
            p.unlink()
        elif p.is_dir():
            shutil.rmtree(p)


def _to_list_of_str(value: Sequence[str]) -> List[str]:
    return [value] if isinstance(value, str) else list(value)
