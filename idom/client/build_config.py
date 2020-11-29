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


ConfigItem = Dict[str, Any]


class BuildConfig:

    __slots__ = "data", "_path", "_item_info"
    _filename = "idom-build-config.json"
    _default_config = {"version": idom.__version__, "items": {}}

    def __init__(self, path: Path) -> None:
        self._path = path / self._filename
        self.data = self._load()
        self._item_info: Dict[str, ConfigItemInfo] = {
            name: derive_config_item_info(item)
            for name, item in self.data["items"].items()
        }

    def update(self, config_items: Iterable[ConfigItem]) -> None:
        for conf in map(validate_config_item, config_items):
            src_name = conf["source_name"]
            self.data["items"][src_name] = conf
            self._item_info[src_name] = derive_config_item_info(conf)

    def has_config_item(self, source_name: str) -> bool:
        return source_name in self.data["items"]

    def get_js_dependency_alias(
        self,
        source_name: str,
        dependency_name: str,
    ) -> Optional[str]:
        try:
            return self._item_info[source_name].js_dependency_aliases[dependency_name]
        except KeyError:
            return None

    def all_aliased_js_dependencies(self) -> List[str]:
        return [
            dep
            for info in self._item_info.values()
            for dep in info.aliased_js_dependencies
        ]

    def all_js_dependency_aliases(self) -> List[str]:
        return [
            alias
            for info in self._item_info.values()
            for alias in info.js_dependency_aliases.values()
        ]

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


def find_python_packages_build_config_items(
    paths: Optional[List[str]] = None,
) -> Tuple[List[ConfigItem], List[Exception]]:
    """Find javascript dependencies declared by Python modules

    Parameters:
        path:
            Search for all importable modules under the given path. Default search
            ``sys.path`` if ``path`` is ``None``.

    Returns:
        Mapping of module names to their corresponding list of discovered dependencies.
    """
    failures: List[Tuple[str, Exception]] = []
    build_configs: List[ConfigItem] = []
    for module_info in iter_modules(paths):
        module_name = module_info.name
        module_loader = module_info.module_finder.find_module(module_name)
        if isinstance(module_loader, SourceFileLoader):
            module_src = module_loader.get_source(module_name)
            try:
                conf = find_build_config_item_in_python_source(module_name, module_src)
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


def find_build_config_item_in_python_file(
    module_name: str, path: Path
) -> Optional[ConfigItem]:
    with path.open() as f:
        return find_build_config_item_in_python_source(module_name, f.read())


def find_build_config_item_in_python_source(
    module_name: str, module_src: str
) -> Optional[ConfigItem]:
    for node in ast.parse(module_src).body:
        if isinstance(node, ast.Assign) and (
            len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "idom_build_config"
        ):
            config_item = validate_config_item(
                eval(compile(ast.Expression(node.value), "temp", "eval"))
            )
            config_item.setdefault("source_name", module_name)
            return config_item

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
        return tuple(pkg.split("@", 1))
    else:
        return pkg, ""


class ConfigItemInfo(NamedTuple):
    js_dependency_aliases: Dict[str, str]
    aliased_js_dependencies: List[str]


def derive_config_item_info(config_item: Dict[str, Any]) -> ConfigItemInfo:
    config_hash = _hash_config_item(config_item)
    alias_suffix = f"{config_item['source_name']}-{config_hash}"
    aliases: Dict[str, str] = {}
    aliased_js_deps: List[str] = []
    for dep in config_item.get("js_dependencies", []):
        dep_name = split_package_name_and_version(dep)[0]
        dep_alias = f"{dep_name}-{alias_suffix}"
        aliases[dep_name] = dep_alias
        aliased_js_deps.append(f"{dep_alias}@npm:{dep}")
    return ConfigItemInfo(
        js_dependency_aliases=aliases,
        aliased_js_dependencies=aliased_js_deps,
    )


def _hash_config_item(config_item: Dict[str, Any]) -> str:
    conf_hash = sha256(json.dumps(config_item, sort_keys=True).encode())
    short_hash_int = (
        int(conf_hash.hexdigest(), 16)
        # chop off the last 8 digits (no need for that many)
        % 10 ** 8
    )
    return format(short_hash_int, "x")


_CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "version": {"type": "string"},
        "items": {
            "type": "object",
            "patternProperties": {".*": {"$ref": "#/definitions/ConfigItem"}},
        },
    },
    "definitions": {
        "ConfigItem": {
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
            },
            "requiredProperties": ["source_name"],
            "additionalProperties": False,
        }
    },
}


_V = TypeVar("_V")


def validate_config(value: _V) -> _V:
    validate_schema(value, _CONFIG_SCHEMA)
    return value


def validate_config_item(value: _V) -> _V:
    validate_schema(value, _CONFIG_SCHEMA["definitions"]["ConfigItem"])
    return value
