import json
import shutil
import subprocess
from loguru import logger
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional, List, Union


CLIENT_DIR = Path(__file__).parent


def import_path(name: str) -> Optional[str]:
    path = CLIENT_DIR / "web_modules"
    for name_part in name.split("/"):
        if not path.is_dir():
            return None
        path /= name_part
    full_path = path.with_suffix(".js")
    if not full_path.is_file():
        return None
    return _web_module(name)


def define_module(name: str, source: str) -> str:
    path = CLIENT_DIR
    for n in ["etc_modules"] + name.split("/"):
        if not path.exists():
            path.mkdir()
        path /= n
    module = path.with_suffix(".js")
    with module.open("w+") as f:
        f.write(source)
    return _etc_module(name)


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
    for path in ["web_modules", "node_modules"]:
        full_path = CLIENT_DIR.joinpath(*path.split("/"))
        if full_path.is_file():
            full_path.unlink()
        elif full_path.is_dir():
            shutil.rmtree(full_path)
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
                "dest": str(CLIENT_DIR / "web_modules"),
                "include": str(CLIENT_DIR / "modules" / "**" / "*.js"),
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


def _web_module(name: str) -> str:
    return f"../web_modules/{name}.js"


def _etc_module(name: str) -> str:
    return f"../etc_modules/{name}.js"
