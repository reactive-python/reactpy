import json
import shutil
import subprocess
from loguru import logger
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional, List, Union, Dict


CLIENT_DIR = Path(__file__).parent

CORE_MODULES = CLIENT_DIR / "core_modules"
NODE_MODULES = CLIENT_DIR / "node_modules"
WEB_MODULES = CLIENT_DIR / "web_modules"


def web_module(name: str) -> str:
    path = f"../{WEB_MODULES.name}/{name}.js"
    if not web_module_exists(name):
        raise ValueError(f"Module '{path}' does not exist.")
    return path


def web_module_path(name: str) -> Optional[Path]:
    return _find_module_os_path(WEB_MODULES, name)


def web_module_exists(name: str) -> bool:
    return _find_module_os_path(WEB_MODULES, name) is not None


def define_web_module(name: str, source: str) -> str:
    path = _create_web_module_os_path(name)
    with path.open("w+") as f:
        f.write(source)
    return web_module(name)


def delete_web_module(name: str) -> None:
    path = _find_module_os_path(WEB_MODULES, name)
    if path is None:
        raise ValueError(f"Module '{name}' does not exist.")
    _delete_os_paths(path)


def install(dependencies: Dict[str, str]) -> None:
    pkg = _package_json()

    npm_install = []
    for dep, import_paths in dependencies.items():
        npm_install.append(dep)
        pkg["snowpack"]["webDependencies"].extend(import_paths.split())

    with TemporaryDirectory() as tempdir:
        tempdir_path = Path(tempdir)

        if NODE_MODULES.exists():
            shutil.copytree(
                NODE_MODULES, tempdir_path / NODE_MODULES.name, symlinks=True
            )

        with (tempdir_path / "package.json").open("w+") as f:
            json.dump(pkg, f)

        _run_subprocess(["npm", "install"], tempdir)
        _run_subprocess(["npm", "install"] + npm_install, tempdir)
        _run_subprocess(["npm", "run", "snowpack"], tempdir)


def restore() -> None:
    _delete_os_paths(WEB_MODULES, NODE_MODULES)
    _run_subprocess(["npm", "install"], CLIENT_DIR)
    _run_subprocess(["npm", "run", "snowpack"], CLIENT_DIR)


def _package_json():
    with (CLIENT_DIR / "package.json").open("r") as f:
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


def _run_subprocess(args: List[str], cwd: Union[str, Path]):
    try:
        subprocess.run(
            args, cwd=cwd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
    except subprocess.CalledProcessError as error:
        if error.stderr is not None:
            logger.error(error.stderr.decode())
        raise


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
