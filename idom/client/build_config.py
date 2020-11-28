from __future__ import annotations

import json
import ast
from copy import deepcopy
from functools import wraps
from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path
from importlib.machinery import SourceFileLoader
from pkgutil import iter_modules
from typing import (
    List,
    Dict,
    Optional,
    Any,
    Iterator,
    Iterable,
    TypeVar,
    Tuple,
    Callable,
    TypedDict,
)

from jsonschema import validate as validate_schema

import idom


_Self = TypeVar("_Self")
_Method = TypeVar("_Method", bound=Callable[..., Any])

BuildConfigItem = Dict[str, Any]


def _requires_open_transaction(method: _Method) -> _Method:
    @wraps(method)
    def wrapper(self: BuildConfig, *args: Any, **kwargs: Any) -> Any:
        if not self._transaction_open:
            raise RuntimeError(
                f"BuildConfig method {method.__name__!r} must be used in a transaction."
            )
        return method(self, *args, **kwargs)

    return wrapper


def _modified_by_transaction(method: _Method) -> _Method:
    @wraps(method)
    def wrapper(self: BuildConfig, *args: Any, **kwargs: Any) -> Any:
        if self._transaction_open:
            raise RuntimeError(
                f"BuildConfig method {method.__name__!r} cannot be used in a transaction."
            )
        return method(self, *args, **kwargs)

    return wrapper


class BuildConfig:

    __slots__ = "config", "_path", "_transaction_open", "_derived_properties"
    _filename = "idom-build-config.json"
    _default_config = {"version": idom.__version__, "by_source": {}}

    def __init__(self, path: Path) -> None:
        self._path = path / self._filename
        self.config = self._load()
        self._derived_properties = derive_config_properties(self.config)
        self._transaction_open = False

    @contextmanager
    def transaction(self: _Self) -> Iterator[_Self]:
        """Open a transaction to modify the config file state"""
        self._transaction_open = True
        old_config = deepcopy(self.config)
        try:
            yield self
        except Exception:
            self.config = old_config
            raise
        else:
            self._save()
            self._derived_properties = derive_config_properties(self.config)
        finally:
            self._transaction_open = False

    @_requires_open_transaction
    def update_config_items(self, config_items: Iterable[BuildConfigItem]) -> None:
        for conf in map(validate_config_item, config_items):
            self.config["by_source"][conf["source_name"]] = conf

    @_modified_by_transaction
    def get_js_dependency_alias(
        self,
        source_name: str,
        dependency_name: str,
    ) -> Optional[str]:
        aliases_by_src = self._derived_properties["js_dependency_aliases_by_source"]
        try:
            return aliases_by_src[source_name][dependency_name]
        except KeyError:
            return None

    @_modified_by_transaction
    def all_aliased_js_dependencies(self) -> List[str]:
        return [
            dep
            for aliased_deps in self._derived_properties[
                "aliased_js_dependencies_by_source"
            ].values()
            for dep in aliased_deps
        ]

    @_modified_by_transaction
    def all_js_dependency_aliases(self) -> List[str]:
        return [
            als
            for aliases in self._derived_properties[
                "js_dependency_aliases_by_source"
            ].values()
            for als in aliases.values()
        ]

    def _load(self) -> Dict[str, Any]:
        if not self._path.exists():
            return deepcopy(self._default_config)
        else:
            with self._path.open() as f:
                return validate_config(
                    json.loads(f.read() or "null") or self._default_config
                )

    def _save(self) -> None:
        with self._path.open("w") as f:
            json.dump(validate_config(self.config), f)

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.config})"


def find_python_packages_build_config_items(
    paths: Optional[List[str]] = None,
) -> Tuple[List[BuildConfigItem], List[Exception]]:
    """Find javascript dependencies declared by Python modules

    Parameters:
        path:
            Search for all importable modules under the given path. Default search
            ``sys.path`` if ``path`` is ``None``.

    Returns:
        Mapping of module names to their corresponding list of discovered dependencies.
    """
    failures: List[Tuple[str, Exception]] = []
    build_configs: List[BuildConfigItem] = []
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
) -> Optional[BuildConfigItem]:
    with path.open() as f:
        return find_build_config_item_in_python_source(module_name, f.read())


def find_build_config_item_in_python_source(
    module_name: str, module_src: str
) -> Optional[BuildConfigItem]:
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


class _DerivedConfigProperties(TypedDict):
    js_dependency_aliases_by_source: Dict[str, Dict[str, str]]
    aliased_js_dependencies_by_source: Dict[str, List[str]]


def derive_config_properties(config: Dict[str, Any]) -> _DerivedConfigProperties:
    js_dependency_aliases_by_source = {}
    aliased_js_dependencies_by_source = {}
    for src, cfg in config["by_source"].items():
        cfg_hash = _hash_config_item(cfg)
        aliases, aliased_js_deps = _config_item_js_dependencies(cfg, cfg_hash)
        js_dependency_aliases_by_source[src] = aliases
        aliased_js_dependencies_by_source[src] = aliased_js_deps
    return {
        "js_dependency_aliases_by_source": js_dependency_aliases_by_source,
        "aliased_js_dependencies_by_source": aliased_js_dependencies_by_source,
    }


def _config_item_js_dependencies(
    config_item: Dict[str, Any], config_hash: str
) -> Tuple[Dict[str, str], List[str]]:
    alias_suffix = f"{config_item['source_name']}-{config_hash}"
    aliases: Dict[str, str] = {}
    aliased_js_deps: List[str] = []
    for dep in config_item.get("js_dependencies", []):
        dep_name = split_package_name_and_version(dep)[0]
        dep_alias = f"{dep_name}-{alias_suffix}"
        aliases[dep_name] = dep_alias
        aliased_js_deps.append(f"{dep_alias}@npm:{dep}")
    return aliases, aliased_js_deps


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
        "by_source": {
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
