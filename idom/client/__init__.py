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
ETC_MODULES = CLIENT_DIR / "etc_modules"


def import_path(prefix: str, name: str) -> str:
    path = f"../{prefix}/{name}.js"
    if not module_exists(prefix, name):
        raise ValueError(f"Module '{path}' does not exist.")
    return path


def define_module(name: str, source: str) -> str:
    path = _create_module_os_path(ETC_MODULES, name)
    with path.open("w+") as f:
        f.write(source)
    return import_path("etc_modules", name)


def delete_module(prefix: str, name: str) -> None:
    path = _find_module_os_path(prefix, name)
    if path is None:
        raise ValueError(f"Module '{import_path(prefix, name)}' does not exist.")
    _delete_os_paths(path)


def module_exists(prefix: Union[str, Path], name: str) -> bool:
    return _find_module_os_path(prefix, name) is not None


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
    _delete_os_paths(WEB_MODULES, NODE_MODULES, ETC_MODULES)
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


def _find_module_os_path(prefix: Union[str, Path], name: str) -> Optional[Path]:
    if isinstance(prefix, str):
        path = CLIENT_DIR / prefix
    else:
        path = prefix
    for name_part in name.split("/"):
        if not path.is_dir():
            return None
        path /= name_part
    full_path = path.with_suffix(".js")
    if not full_path.is_file():
        return None
    return full_path


def _create_module_os_path(prefix: Union[str, Path], name: str) -> Path:
    if isinstance(prefix, str):
        path = CLIENT_DIR / prefix
    else:
        path = prefix
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
