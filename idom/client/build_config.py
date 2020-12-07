from __future__ import annotations

import json
import ast
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from importlib.machinery import SourceFileLoader
from pkgutil import iter_modules
from typing import (
    List,
    Dict,
    Optional,
    Any,
    Iterable,
    TypeVar,
    Tuple,
    NamedTuple,
)

from jsonschema import validate as validate_schema

import idom


ConfigEntry = Dict[str, Any]


class BuildConfig:

    __slots__ = "data", "_path", "_entry_info"
    _filename = "idom-build-config.json"
    _default_config = {"version": idom.__version__, "entries": {}}

    def __init__(self, path: Path) -> None:
        self._path = path / self._filename
        self.data = self._load()
        self._entry_info: Dict[str, ConfigEntryInfo] = {
            name: derive_config_entry_info(entry)
            for name, entry in self.data["entries"].items()
        }

    def get_entry(self, source_name: str) -> ConfigEntry:
        return self.data["entries"][source_name]

    def get_entry_info(self, source_name: str) -> "ConfigEntryInfo":
        return self._entry_info[source_name]

    def clear_entries(self) -> None:
        self.data["entries"].clear()
        self._entry_info.clear()

    def update_entries(self, config_entries: Iterable[Dict[str, Any]]) -> None:
        # a useful debug assertion - the error which would result otherwise is confusing
        assert not isinstance(config_entries, dict), "expected list, not a dict"

        for conf in map(
            # BUG: https://github.com/python/mypy/issues/6697
            validate_config_entry,  # type: ignore
            config_entries,
        ):
            src_name = conf["source_name"]
            self.data["entries"][src_name] = conf
            self._entry_info[src_name] = derive_config_entry_info(conf)

    def has_entry(self, source_name: str) -> bool:
        return source_name in self.data["entries"]

    def entry_has_dependency(self, source_name: str, dependency: str) -> bool:
        name, _ = split_package_name_and_version(dependency)
        entry_info = self.get_entry_info(source_name)
        return (
            name in entry_info.js_dependency_aliases
            or name == entry_info.js_package_def.name
        )

    def resolve_js_dependency_name(
        self,
        source_name: str,
        dependency_name: str,
    ) -> Optional[str]:
        try:
            info = self._entry_info[source_name]
        except KeyError:
            return None
        if info.js_package_def is not None:
            if info.js_package_def.name != dependency_name:
                return None
            else:
                return dependency_name
        else:
            try:
                return info.js_dependency_aliases[dependency_name]
            except KeyError:
                return None

    def all_js_dependencies(self) -> List[str]:
        deps: List[str] = []
        for info in self._entry_info.values():
            if info.js_package_def is not None:
                deps.append(str(info.js_package_def.path))
            else:
                deps.extend(info.aliased_js_dependencies)
        return deps

    def all_js_dependency_names(self) -> List[str]:
        names: List[str] = []
        for info in self._entry_info.values():
            if info.js_package_def is not None:
                names.append(info.js_package_def.name)
            else:
                names.extend(info.js_dependency_aliases.values())
        return names

    def save(self) -> None:
        with self._path.open("w") as f:
            json.dump(validate_config(self.data), f)

    def _load(self) -> Dict[str, Any]:
        if not self._path.exists():
            return deepcopy(self._default_config)
        else:
            with self._path.open() as f:
                return validate_config(
                    json.loads(f.read() or "null") or self._default_config
                )

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.data})"


def find_python_packages_build_config_entries(
    paths: Optional[List[str]] = None,
) -> Tuple[List[ConfigEntry], List[Exception]]:
    """Find javascript dependencies declared by Python modules

    Parameters:
        path:
            Search for all importable modules under the given path. Default search
            ``sys.path`` if ``path`` is ``None``.

    Returns:
        Mapping of module names to their corresponding list of discovered dependencies.
    """
    failures: List[Exception] = []
    build_configs: List[ConfigEntry] = []
    for module_info in iter_modules(paths):
        module_name = module_info.name
        module_loader = module_info.module_finder.find_module(module_name)
        if isinstance(module_loader, SourceFileLoader):
            try:
                module_filename = module_loader.get_filename(module_name)
                if isinstance(module_filename, bytes):  # pragma: no cover
                    module_filename = module_filename.decode()
                conf = find_build_config_entry_in_python_file(
                    module_name, Path(module_filename)
                )
            except Exception as cause:
                error = RuntimeError(
                    f"Failed to load build config for module {module_name!r}"
                )
                error.__cause__ = cause
                failures.append(error)
            else:
                if conf is not None:
                    build_configs.append(conf)
    return build_configs, failures


def find_build_config_entry_in_python_file(
    module_name: str, module_path: Path
) -> Optional[ConfigEntry]:
    with module_path.open() as f:
        module_src = f.read()

    for node in ast.parse(module_src).body:
        if isinstance(node, ast.Assign) and (
            len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "idom_build_config"
        ):
            config_entry = validate_config_entry(
                {
                    "source_name": module_name,
                    **eval(
                        compile(
                            source=ast.Expression(node.value),
                            filename=str(module_path),
                            mode="eval",
                        ),
                    ),
                }
            )
            if "js_package" in config_entry:
                js_pkg = module_path.parent.joinpath(
                    *config_entry["js_package"].split("/")
                )
                config_entry["js_package"] = str(js_pkg.resolve().absolute())
            config_entry.setdefault("source_name", module_name)
            return config_entry

    return None


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


class JsPackageDef(NamedTuple):
    path: Path
    name: str


class ConfigEntryInfo(NamedTuple):
    js_dependency_aliases: Dict[str, str]
    aliased_js_dependencies: List[str]
    js_package_def: Optional[JsPackageDef]


def derive_config_entry_info(config_entry: Dict[str, Any]) -> ConfigEntryInfo:
    config_hash = _hash_config_entry(config_entry)
    alias_suffix = f"{config_entry['source_name']}-{config_hash}"
    aliases: Dict[str, str] = {}
    aliased_js_deps: List[str] = []
    for dep in config_entry.get("js_dependencies", []):
        dep_name = split_package_name_and_version(dep)[0]
        dep_alias = f"{dep_name}-{alias_suffix}"
        aliases[dep_name] = dep_alias
        aliased_js_deps.append(f"{dep_alias}@npm:{dep}")

    js_pkg_def: Optional[JsPackageDef]
    if "js_package" in config_entry:
        js_pkg_path = Path(config_entry["js_package"])
        js_pkg_json = js_pkg_path / "package.json"
        try:
            with js_pkg_json.open() as f:
                js_pkg_name = str(json.load(f)["name"])
        except FileNotFoundError as error:
            raise ValueError(
                f"Path to package {str(js_pkg_json)!r} specified by "
                f"{config_entry['source_name']!r} does not exist"
            ) from error
        else:
            js_pkg_def = JsPackageDef(path=js_pkg_path, name=js_pkg_name)
    else:
        js_pkg_def = None

    return ConfigEntryInfo(
        js_dependency_aliases=aliases,
        aliased_js_dependencies=aliased_js_deps,
        js_package_def=js_pkg_def,
    )


def _hash_config_entry(config_entry: Dict[str, Any]) -> str:
    conf_hash = sha256(json.dumps(config_entry, sort_keys=True).encode())
    short_hash_int = (
        int(conf_hash.hexdigest(), 16)
        # chop off the last 8 digits (no need for that many)
        % 10 ** 8
    )
    return format(short_hash_int, "x")


_CONFIG_SCHEMA: Any = {
    "type": "object",
    "properties": {
        "version": {"type": "string"},
        "entries": {
            "type": "object",
            "patternProperties": {".*": {"$ref": "#/definitions/ConfigEntry"}},
        },
    },
    "definitions": {
        "ConfigEntry": {
            "type": "object",
            "properties": {
                "source_name": {
                    "type": "string",
                    "pattern": r"^[\w\d\-\.]+$",
                },
                "js_dependencies": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "js_package": {"type": "string"},
            },
            "required": ["source_name"],
            "dependencies": {
                "js_dependencies": {"not": {"required": ["js_package"]}},
                "js_package": {"not": {"required": ["js_dependencies"]}},
            },
            "additionalProprties": False,
        }
    },
}
_CONFIG_ITEM_SCHEMA = _CONFIG_SCHEMA["definitions"]["ConfigEntry"]


_V = TypeVar("_V", bound=Any)


def validate_config(value: _V) -> _V:
    validate_schema(value, _CONFIG_SCHEMA)
    return value


def validate_config_entry(value: _V) -> _V:
    validate_schema(value, _CONFIG_ITEM_SCHEMA)
    return value
