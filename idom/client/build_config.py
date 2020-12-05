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

    def clear_items(self) -> None:
        self.data["items"].clear()
        self._item_info.clear()

    def update_items(self, config_items: Iterable[Dict[str, Any]]) -> None:
        # a useful debug assertion - the error which would result otherwise is confusing
        assert not isinstance(config_items, dict), "expected list, not a dict"

        for conf in map(
            # BUG: https://github.com/python/mypy/issues/6697
            validate_config_item,  # type: ignore
            config_items,
        ):
            src_name = conf["source_name"]
            self.data["items"][src_name] = conf
            self._item_info[src_name] = derive_config_item_info(conf)

    def has_config_item(self, source_name: str) -> bool:
        return source_name in self.data["items"]

    def resolve_js_dependency_name(
        self,
        source_name: str,
        dependency_name: str,
    ) -> Optional[str]:
        info = self._item_info[source_name]
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
        for info in self._item_info.values():
            if info.js_package_def is not None:
                deps.append(str(info.js_package_def.path))
            else:
                deps.extend(info.aliased_js_dependencies)
        return deps

    def all_js_dependency_names(self) -> List[str]:
        names: List[str] = []
        for info in self._item_info.values():
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
            try:
                conf = find_build_config_item_in_python_file(
                    module_name, Path(module_loader.get_filename(module_name))
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


def find_build_config_item_in_python_file(
    module_name: str, module_path: Path
) -> Optional[ConfigItem]:
    with module_path.open() as f:
        module_src = f.read()

    for node in ast.parse(module_src).body:
        if isinstance(node, ast.Assign) and (
            len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "idom_build_config"
        ):
            config_item = validate_config_item(
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
            if "js_package" in config_item:
                js_pkg = module_path.parent.joinpath(
                    *config_item["js_package"].split("/")
                )
                config_item["js_package"] = str(js_pkg.resolve().absolute())
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


class JsPackageDef(NamedTuple):
    path: Path
    name: str


class ConfigItemInfo(NamedTuple):
    js_dependency_aliases: Dict[str, str]
    aliased_js_dependencies: List[str]
    js_package_def: Optional[JsPackageDef]


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

    if "js_package" in config_item:
        js_pkg_path = Path(config_item["js_package"])
        js_pkg_json = js_pkg_path / "package.json"
        try:
            with js_pkg_json.open() as f:
                js_pkg_name = str(json.load(f)["name"])
        except FileNotFoundError as error:
            raise ValueError(
                f"Path to package {str(js_pkg_json)!r} specified by "
                f"{config_item['source_name']!r} does not exist"
            ) from error
        else:
            js_pkg_info = JsPackageDef(path=js_pkg_path, name=js_pkg_name)
    else:
        js_pkg_info = None

    return ConfigItemInfo(
        js_dependency_aliases=aliases,
        aliased_js_dependencies=aliased_js_deps,
        js_package_def=js_pkg_info,
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


_V = TypeVar("_V", bound=Any)


def validate_config(value: _V) -> _V:
    validate_schema(value, _CONFIG_SCHEMA)
    return value


def validate_config_item(value: _V) -> _V:
    validate_schema(value, _CONFIG_SCHEMA["definitions"]["ConfigItem"])
    return value
