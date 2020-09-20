import json
import shutil
import subprocess
from loguru import logger
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional, List, Union, Dict, Sequence

from .utils import Spinner


APP_DIR = Path(__file__).parent / "app"
BUILD_DIR = APP_DIR / "build"
WEB_MODULES_DIR = BUILD_DIR / "web_modules"


STATIC_SHIMS: Dict[str, Path] = {}


def find_path(url_path: str) -> Optional[Path]:
    url_path = url_path.strip("/")

    builtin_path = BUILD_DIR.joinpath(*url_path.split("/"))
    if builtin_path.exists():
        return builtin_path

    return STATIC_SHIMS.get(url_path)


def web_module_url(name: str) -> str:
    path = f"../{WEB_MODULES_DIR.name}/{name}.js"
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
        raise ValueError(f"Web module source {source} does not exist or is not a file")
    STATIC_SHIMS[f"web_modules/{name}.js"] = source_path
    return web_module_url(name)


def delete_web_modules(names: Sequence[str], skip_missing: bool = False) -> None:
    paths = []
    cache = Cache(BUILD_DIR)
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

        cache.delete_package(name, skip_missing)

    for p in paths:
        _delete_os_paths(p)

    cache.save()


def installed() -> List[str]:
    names: List[str] = []
    for path in WEB_MODULES_DIR.rglob("*.js"):
        rel_path = path.relative_to(WEB_MODULES_DIR)
        if rel_path.parent.name != "common":
            names.append(str(rel_path.with_suffix("")))
    return list(sorted(names))


def install(
    packages: Sequence[str], exports: Sequence[str] = (), show_spinner: bool = False
) -> None:
    with TemporaryDirectory() as tempdir:
        tempdir_path = Path(tempdir)
        temp_static_dir = tempdir_path / "static"
        temp_build_dir = temp_static_dir / "build"

        # copy over the whole ./static directory into the temp one
        shutil.copytree(APP_DIR, temp_static_dir, symlinks=True)

        cache = Cache(temp_build_dir)
        cache.add_packages(packages, exports)

        with open(temp_static_dir / "package.json") as f:
            package_json = json.load(f)

        pkg_snowpack = package_json.setdefault("snowpack", {})
        pkg_snowpack.setdefault("install", []).extend(cache.export_list)

        with (temp_static_dir / "package.json").open("w+") as f:
            json.dump(package_json, f)

        with Spinner(f"Installing: {', '.join(packages)}", show=show_spinner):
            _run_subprocess(["npm", "install"], temp_static_dir)
            _run_subprocess(["npm", "install"] + cache.package_list, temp_static_dir)
            _run_subprocess(["npm", "run", "build"], temp_static_dir)

        cache.save()

        if BUILD_DIR.exists():
            shutil.rmtree(BUILD_DIR)

        shutil.copytree(temp_build_dir, BUILD_DIR, symlinks=True)


def restore(show_spinner: bool = False) -> None:
    with Spinner("Restoring", show=show_spinner):
        _delete_os_paths(BUILD_DIR)
        _run_subprocess(["npm", "install"], APP_DIR)
        _run_subprocess(["npm", "run", "build"], APP_DIR)
    STATIC_SHIMS.clear()


class Cache:
    """Manages a cache file stored at ``build/.idom-cache.json``"""

    __slots__ = "_file", "package_list", "export_list"

    def __init__(self, path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True)
        self._file = path / ".idom-cache.json"
        if not self._file.exists():
            self.package_list: List[str] = []
            self.export_list: List[str] = []
        else:
            self._load()

    def add_packages(self, packages: Sequence[str], exports: Sequence[str]) -> None:
        package_list = _to_list_of_str(packages)
        export_list = _to_list_of_str(exports)
        export_list.extend(map(_export_name_from_package, package_list))
        self.package_list = list(set(self.package_list + package_list))
        self.export_list = list(set(self.export_list + export_list))

    def delete_package(self, export_name: str, skip_missing: bool) -> None:
        if export_name in self.export_list:
            self.export_list.remove(export_name)
            for i, pkg in enumerate(self.package_list):
                if _export_name_from_package(pkg) == export_name:
                    del self.package_list[i]
                    break

    def save(self) -> None:
        cache = {
            name: getattr(self, name)
            for name in self.__slots__
            if not name.startswith("_")
        }
        with self._file.open("w+") as f:
            json.dump(cache, f)

    def _load(self) -> None:
        with self._file.open() as f:
            cache = json.load(f)
            for name in self.__slots__:
                if not name.startswith("_"):
                    setattr(self, name, cache[name])


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


def _export_name_from_package(pkg: str) -> str:
    at_count = pkg.count("@")
    if pkg.startswith("@") and at_count == 1:
        return pkg
    else:
        # this works even if there are no @ symbols
        return pkg.rsplit("@", 1)[0]
