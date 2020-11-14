import json
import ast
from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path
from importlib.machinery import SourceFileLoader
from pkgutil import iter_modules
from typing import List, Dict, Optional, Any, NamedTuple, Iterable, Iterator, TypeVar

from .utils import split_package_name_and_version

from idom.cli import console


class BuildConfigFile:

    __slots__ = "configs", "_path"
    _filename = ".idom-build-configs.json"

    def __init__(self, path: Path) -> None:
        self._path = path / self._filename
        self.configs = self._load_configs()

    @contextmanager
    def transaction(self) -> Iterator[None]:
        old_configs = self.configs
        self.configs = old_configs.copy()
        try:
            yield
        except Exception:
            self.configs = old_configs
            raise
        else:
            self.save()

    def add(self, build_configs: Iterable[Any], ignore_existing: bool = False) -> None:
        for config in map(BuildConfigItem.cast, build_configs):
            source_name = config.source_name
            if not ignore_existing and source_name in self.configs:
                raise ValueError(f"A build config for {source_name!r} already exists")
            self.configs[source_name] = config
        return None

    def save(self) -> None:
        with self._path.open("w") as f:
            json.dump({name: conf._asdict() for name, conf in self.configs.items()}, f)

    def show(self, indent: int = 2) -> str:
        return json.dumps(
            {name: conf._asdict() for name, conf in self.configs.items()},
            indent=indent,
        )

    def clear(self) -> None:
        self.configs = {}

    def _load_configs(self) -> Dict[str, "BuildConfigItem"]:
        if not self._path.exists():
            return {}
        with self._path.open() as f:
            content = f.read()
            if not content:
                return {}
            else:
                return {n: BuildConfigItem(**c) for n, c in json.loads(content).items()}

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.show(indent=0)})"


_Class = TypeVar("_Class")
_Self = TypeVar("_Self")


class BuildConfigItem(NamedTuple):
    """Describes build requirements for a Python package or application"""

    @classmethod
    def cast(cls: _Class, value: Any, source_name: Optional[str] = None) -> _Class:
        if isinstance(value, cls):
            return value
        elif isinstance(value, tuple):
            return cls(*value)._validate()
        elif isinstance(value, dict):
            if source_name is not None:
                value = {"source_name": source_name, **value}
            return cls(**value)._validate()
        else:
            raise ValueError(f"Expected a dict or tuple, not {value!r}")

    source_name: str
    js_dependencies: List[str]

    def identifier(self) -> str:
        conf_hash = sha256(json.dumps(self).encode()).hexdigest()
        return f"{self.source_name}-{conf_hash[:8]}"

    def get_js_dependency_alias(self, name: str) -> str:
        return f"{name}-{self.identifier()}"

    def aliased_js_dependencies(self) -> List[str]:
        idf = self.identifier()
        aliased_dependencies: List[str] = []
        for dep in self.js_dependencies:
            name = split_package_name_and_version(dep)[0]
            aliased_dependencies.append(f"{name}-{idf}@npm:{dep}")
        return aliased_dependencies

    def _validate(self: _Self) -> _Self:
        if not isinstance(self.source_name, str):
            raise ValueError(
                f"'source_name' must be a string, not {self.source_name!r}"
            )
        if not isinstance(self.js_dependencies, list):
            raise ValueError(
                f"'js_dependencies' must be a list, not {self.js_dependencies!r}"
            )
        for item in self.js_dependencies:
            if not isinstance(item, str):
                raise ValueError(
                    f"items of 'js_dependencies' must be strings, not {item!r}"
                )
        return self


def find_build_config_item_in_python_source(
    module_name: str, path: Path
) -> Optional[BuildConfigItem]:
    with path.open() as f:
        return _parse_build_config_item_from_python_source(module_name, f.read())


def find_python_packages_build_config_items(
    path: Optional[str] = None,
) -> List[BuildConfigItem]:
    """Find javascript dependencies declared by Python modules

    Parameters:
        path:
            Search for all importable modules under the given path. Default search
            ``sys.path`` if ``path`` is ``None``.

    Returns:
        Mapping of module names to their corresponding list of discovered dependencies.
    """
    build_configs: List[BuildConfigItem] = []
    for module_info in iter_modules(path):
        module_loader = module_info.module_finder.find_module(module_info.name)
        if isinstance(module_loader, SourceFileLoader):
            module_src = module_loader.get_source(module_info.name)
            conf = _parse_build_config_item_from_python_source(
                module_info.name, module_src
            )
            if conf is not None:
                build_configs.append(conf)
    return build_configs


def _parse_build_config_item_from_python_source(
    module_name: str, module_src: str
) -> Optional[BuildConfigItem]:
    for node in ast.parse(module_src).body:
        if isinstance(node, ast.Assign) and (
            len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "idom_build_config"
        ):
            try:
                raw_config = eval(compile(ast.Expression(node.value), "temp", "eval"))
            except Exception as error:
                _echo_error(
                    f"Failed to load 'idom_build_config' for {module_name!r} because {error!r}"
                )
                return None

            try:
                return BuildConfigItem.cast(raw_config, module_name)
            except ValueError as error:
                _echo_error(
                    f"Failed to load build config for {module_name!r} because {error}"
                )
                return None
    return None


def _echo_error(msg: str) -> None:
    console.echo(msg, color="red")
