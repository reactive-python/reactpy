import json
import shutil
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional, List, Union, Dict, Sequence

from .utils import find_idom_js_dependencies_from_python_packages, spinner


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


def uninstall(names: List[str], skip_missing: bool = False) -> None:
    paths = []
    cache = Cache(BUILD_DIR)
    for name in names:
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


def install(packages: List[str]) -> None:

    with TemporaryDirectory() as tempdir:
        tempdir_path = Path(tempdir)
        temp_app_dir = tempdir_path / "static"
        temp_build_dir = temp_app_dir / "build"
        cache = Cache(BUILD_DIR)

        # copy over the whole APP_DIR directory into the temp one
        shutil.copytree(APP_DIR, temp_app_dir, symlinks=True)

        if packages:
            with spinner(f"Installing {', '.join(packages)}"):
                _npm_install(packages, temp_app_dir)

        for pkg in packages:
            cache.delete_package(pkg, skip_missing=True)

        pkgs_from_cache = cache.package_list()
        if pkgs_from_cache:
            plural_s = "" if len(pkgs_from_cache) == 1 else "s"
            with spinner(f"Reinstalling {len(pkgs_from_cache)} package{plural_s}"):
                _npm_install(pkgs_from_cache, temp_app_dir)

        py_pkg_deps = _get_py_pkg_deps_to_install()
        if py_pkg_deps:
            for mod_name, mod_deps in py_pkg_deps.items():
                with spinner(f"Installing dependencies of {mod_name!r}"):
                    _npm_install(mod_deps, temp_app_dir)

        with spinner("Building client"):
            _run_subprocess(["npm", "run", "build"], temp_app_dir)

        # finally save installed user packages
        cache.add_packages(packages)
        cache.save()

        if BUILD_DIR.exists():
            shutil.rmtree(BUILD_DIR)

        shutil.copytree(temp_build_dir, BUILD_DIR, symlinks=True)


def restore() -> None:
    with spinner("Restoring"):
        _delete_os_paths(BUILD_DIR)
        _run_subprocess(["npm", "install"], APP_DIR)
        _run_subprocess(["npm", "run", "build"], APP_DIR)
        STATIC_SHIMS.clear()


class Cache:
    """Manages a cache file stored at ``build/.idom-cache.json``"""

    __slots__ = "_file", "package_name_to_requirement"

    def __init__(self, path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True)
        self._file = path / ".idom-cache.json"
        if not self._file.exists():
            self.package_name_to_requirement: Dict[str, str] = {}
        else:
            self._load()

    def package_list(self) -> List[str]:
        return list(self.package_name_to_requirement.values())

    def add_packages(self, packages: List[str]) -> None:
        for pkg in packages:
            self.package_name_to_requirement[_export_name_from_package(pkg)] = pkg

    def delete_package(self, name: str, skip_missing: bool) -> None:
        name = _export_name_from_package(name)
        if name in self.package_name_to_requirement:
            del self.package_name_to_requirement[name]
        elif not skip_missing:
            raise ValueError(f"{name!r} is not installed.")

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


def _npm_install(packages: Sequence[str], cwd: Union[str, Path]) -> None:
    _run_subprocess(["npm", "install"] + packages, cwd)


def _run_subprocess(args: List[str], cwd: Union[str, Path]) -> None:
    try:
        subprocess.run(
            args, cwd=cwd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
    except subprocess.CalledProcessError as error:
        raise RuntimeError(error.stderr.decode())
    return None


def _delete_os_paths(*paths: Path) -> None:
    for p in paths:
        if p.is_file():
            p.unlink()
        elif p.is_dir():
            shutil.rmtree(p)


def _export_name_from_package(pkg: str) -> str:
    at_count = pkg.count("@")
    if pkg.startswith("@") and at_count == 1:
        return pkg
    else:
        # this works even if there are no @ symbols
        return pkg.rsplit("@", 1)[0]


def _get_py_pkg_deps_to_install() -> Dict[str, List[str]]:
    already_installed = set(installed())

    py_pkg_deps: Dict[str, List[str]] = {}
    for mod_name, mod_deps in find_idom_js_dependencies_from_python_packages().items():
        mod_deps_to_install = set(mod_deps).difference(already_installed)
        if mod_deps_to_install:
            py_pkg_deps[mod_name] = list(mod_deps_to_install)

    return py_pkg_deps
