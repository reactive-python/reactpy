from __future__ import annotations

import json
import ast
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
    Iterable,
    Iterator,
    TypeVar,
    Tuple,
    Callable,
)

from .utils import split_package_name_and_version


_Self = TypeVar("_Self")
_Class = TypeVar("_Class")
_Method = TypeVar("_Method", bound=Callable[..., Any])


def _requires_open_transaction(method: _Method) -> _Method:
    @wraps(method)
    def wrapper(self: BuildConfigFile, *args: Any, **kwargs: Any) -> Any:
        if not self._transaction_open:
            raise RuntimeError("Cannot modify BuildConfigFile without transaction.")
        return method(self, *args, **kwargs)

    return wrapper


class BuildConfigFile:

    __slots__ = "_config_items", "_path", "_transaction_open"
    _filename = "idom-build-config.json"

    def __init__(self, path: Path) -> None:
        self._path = path / self._filename
        self._config_items = self._load_config_items()
        self._transaction_open = False

    @contextmanager
    def transaction(self: _Self) -> Iterator[_Self]:
        """Open a transaction to modify the config file state"""
        self._transaction_open = True
        old_configs = self._config_items
        self._config_items = old_configs.copy()
        try:
            yield self
        except Exception:
            self._config_items = old_configs
            raise
        else:
            self.save()
        finally:
            self._transaction_open = False

    @property
    def configs(self) -> Dict[str, "BuildConfigItem"]:
        """A dictionary of config items"""
        return self._config_items.copy()

    def save(self) -> None:
        """Save config state to file"""
        with self._path.open("w") as f:
            json.dump(self.to_dicts(), f)

    def to_dicts(self) -> Dict[str, Dict[str, Any]]:
        """Return string repr of config state"""
        return {name: conf.to_dict() for name, conf in self._config_items.items()}

    @_requires_open_transaction
    def add(self, build_configs: Iterable[Any], ignore_existing: bool = False) -> None:
        """Add a config item"""
        for config in map(to_build_config_item, build_configs):
            source_name = config.source_name
            if not ignore_existing and source_name in self._config_items:
                raise ValueError(f"A build config for {source_name!r} already exists")
            self._config_items[source_name] = config
        return None

    @_requires_open_transaction
    def remove(self, source_name: str, ignore_missing: bool = False) -> None:
        """Remove a config item"""
        if ignore_missing:
            self._config_items.pop(source_name, None)
        else:
            del self._config_items[source_name]

    @_requires_open_transaction
    def clear(self) -> None:
        """Clear all config items"""
        self._config_items = {}

    def _load_config_items(self) -> Dict[str, "BuildConfigItem"]:
        if not self._path.exists():
            return {}
        with self._path.open() as f:
            content = f.read().strip() or "{}"
            return {n: BuildConfigItem(**c) for n, c in json.loads(content).items()}

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.to_dicts()})"


def _save_init_params(init_method: _Method) -> _Method:
    @wraps(init_method)
    def wrapper(self: Any, **kwargs: Any) -> None:
        self._init_params = kwargs
        init_method(self, **kwargs)
        return None

    return wrapper


def to_build_config_item(value: Any) -> "BuildConfigItem":
    if isinstance(value, dict):
        return BuildConfigItem.from_dict(value)
    elif isinstance(value, BuildConfigItem):
        return value
    else:
        raise ValueError(f"Expected a BuildConfigItem or dict, not {value!r}")


class BuildConfigItem:
    """Describes build requirements for a Python package or application

    Attributes:
        source_name:
            The name of the source where this config came from (usually a Python module)
        js_dependencies:
            A list of dependency specifiers which can be installed by NPM. The
            specifiers give each dependency an alias to avoid name and version
            clashes that might occur between configs.
        js_dependency_aliases:
            Maps the name of a dependency to the alias used in ``js_dependencies``
    """

    __slots__ = (
        "_init_params",
        "source_name",
        "identifier",
        "js_dependencies",
        "js_dependency_aliases",
        "js_dependency_alias_suffix",
    )

    @_save_init_params
    def __init__(self, source_name: str, js_dependencies: List[str]) -> None:
        if not isinstance(source_name, str):
            raise ValueError(f"'source_name' must be a string, not {source_name!r}")
        if not isinstance(js_dependencies, list):
            raise ValueError(
                f"'js_dependencies' must be a list, not {js_dependencies!r}"
            )
        for item in js_dependencies:
            if not isinstance(item, str):
                raise ValueError(
                    f"items of 'js_dependencies' must be strings, not {item!r}"
                )

        self.source_name = source_name
        self.js_dependencies: List[str] = []
        self.js_dependency_aliases: Dict[str, str] = {}
        self.js_dependency_alias_suffix = f"{source_name}-{format(hash(self), 'x')}"

        for dep in js_dependencies:
            dep_name = split_package_name_and_version(dep)[0]
            dep_alias = f"{dep_name}-{self.js_dependency_alias_suffix}"
            self.js_dependencies.append(f"{dep_alias}@npm:{dep}")
            self.js_dependency_aliases[dep_name] = dep_alias

    @classmethod
    def from_dict(cls: _Class, value: Any, source_name: Optional[str] = None) -> _Class:
        if not isinstance(value, dict):
            raise ValueError(f"Expected build config to be a dict, not {value!r}")
        if source_name is not None:
            value.setdefault("source_name", source_name)
        return cls(**value)

    def to_dict(self) -> Dict[str, Any]:
        return self._init_params.copy()

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, type(self)) and (other.to_dict() == self.to_dict())

    def __hash__(self) -> int:
        sorted_params = {k: self._init_params[k] for k in sorted(self._init_params)}
        param_hash = sha256(json.dumps(sorted_params).encode())
        return (
            int(param_hash.hexdigest(), 16)
            # chop off the last 8 digits (no need for that many)
            % 10 ** 8
        )

    def __repr__(self) -> str:
        items = ", ".join(f"{k}={v!r}" for k, v in self.to_dict().items())
        return f"{type(self).__name__}({items})"


def find_build_config_item_in_python_file(
    module_name: str, path: Path
) -> Optional[BuildConfigItem]:
    with path.open() as f:
        return find_build_config_item_in_python_source(module_name, f.read())


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


def find_build_config_item_in_python_source(
    module_name: str, module_src: str
) -> Optional[BuildConfigItem]:
    for node in ast.parse(module_src).body:
        if isinstance(node, ast.Assign) and (
            len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "idom_build_config"
        ):
            raw_config = eval(compile(ast.Expression(node.value), "temp", "eval"))
            return BuildConfigItem.from_dict(raw_config, source_name=module_name)
    return None
