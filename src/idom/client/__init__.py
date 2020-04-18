import json
import shutil
import subprocess
from loguru import logger
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional, List, Union


CLIENT_DIR = Path(__file__).parent

CORE_MODULES = CLIENT_DIR / "core_modules"
NODE_MODULES = CLIENT_DIR / "node_modules"
WEB_MODULES = CLIENT_DIR / "web_modules"
ETC_MODULES = CLIENT_DIR / "etc_modules"


def import_path(prefix: str, name: str) -> Optional[str]:
    if not module_exists(prefix, name):
        raise ValueError(f"Module '{_module_js_path(prefix, name)}' does not exist.")
    return _module_js_path(prefix, name)


def define_module(name: str, source: str) -> str:
    path = _create_module_os_path(ETC_MODULES, name)
    with path.open("w+") as f:
        f.write(source)
    return _module_js_path("etc_modules", name)


def delete_module(prefix: str, name: str) -> None:
    if not module_exists(prefix, name):
        raise ValueError(f"Module '{_module_js_path(prefix, name)}' does not exist.")
    return None


def module_exists(prefix: Union[str, Path], name: str) -> bool:
    return _find_module_os_path(prefix, name) is not None


def install(*dependencies: str) -> None:
    pkg = _package_json()

    npm_install = []
    for dep in dependencies:
        install_spec, *import_paths = dep.split(" ")
        if not import_paths:
            raise ValueError(
                "Expected a space seperated string where an installation "
                f"spec is followed by at least on import path, not '{dep}'"
            )
        pkg["snowpack"]["webDependencies"].extend(import_paths)
        npm_install.append(install_spec)

    with TemporaryDirectory() as tempdir:
        with (Path(tempdir) / "package.json").open("w+") as f:
            json.dump(pkg, f)

        _run_subprocess(["npm", "install"], tempdir)
        if npm_install:
            _run_subprocess(["npm", "install"] + npm_install, tempdir)
        _run_subprocess(["npm", "run", "snowpack"], tempdir)


def restore() -> None:
    _delete_os_paths(WEB_MODULES, NODE_MODULES, ETC_MODULES)
    install()


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
        logger.error(error.stderr.decode())
        raise


def _module_js_path(prefix: str, name: str) -> str:
    return f"../{prefix}/{name}.js"


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
