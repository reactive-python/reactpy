import json
import ast
from hashlib import sha256
from pathlib import Path
from importlib.machinery import SourceFileLoader
from pkgutil import iter_modules
from typing import List, Dict, Optional, Any, NamedTuple

from .sh import echo
from .utils import split_package_name_and_version


class BuildConfig(NamedTuple):

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


def save_build_configs(path: Path, configs: Dict[str, BuildConfig]) -> None:
    with (path / ".idom-build-configs.json").open("w") as f:
        json.dump(configs, f)


def load_build_configs(path: Path) -> Dict[str, BuildConfig]:
    fname = path / ".idom-build-configs.json"
    if not fname.exists():
        return {}
    with fname.open() as f:
        content = f.read()
        if not content:
            return {}
        else:
            return {n: BuildConfig(*c) for n, c in json.loads(content).items()}


def to_build_config(config: Any, source_name: Optional[str] = None) -> BuildConfig:
    if isinstance(config, BuildConfig):
        return config

    if not isinstance(config, dict):
        raise ValueError(
            f"build config must be a dictionary, but found {type(config).__name__}",
        )

    source_name = config.get("source_name", source_name)
    if not isinstance(source_name, str):
        raise ValueError(
            f"'source_name' must be a string, not {type(source_name).__name__}"
        )

    js_dependencies = config.get("js_dependencies")
    if not isinstance(js_dependencies, list):
        raise ValueError(
            f"'js_dependencies' must be a list, not {type(js_dependencies).__name__}"
        )
    for item in js_dependencies:
        if not isinstance(item, str):
            raise ValueError(
                f"items of 'js_dependencies' must be strings, not {type(item).__name__}"
            )

    return BuildConfig(source_name=source_name, js_dependencies=js_dependencies)


def find_build_config_in_python_source(
    module_name: str, path: Path
) -> Optional[BuildConfig]:
    with path.open() as f:
        return _parse_build_config_from_python_source(module_name, f.read())


def find_python_packages_build_configs(
    path: Optional[str] = None,
) -> Dict[str, BuildConfig]:
    """Find javascript dependencies declared by Python modules

    Parameters:
        path:
            Search for all importable modules under the given path. Default search
            ``sys.path`` if ``path`` is ``None``.

    Returns:
        Mapping of module names to their corresponding list of discovered dependencies.
    """
    build_configs: Dict[str, BuildConfig] = {}
    for module_info in iter_modules(path):
        module_loader = module_info.module_finder.find_module(module_info.name)
        if isinstance(module_loader, SourceFileLoader):
            module_src = module_loader.get_source(module_info.name)
            conf = _parse_build_config_from_python_source(module_info.name, module_src)
            if conf is not None:
                build_configs[conf.source_name] = conf
    return build_configs


def _parse_build_config_from_python_source(
    module_name: str, module_src: str
) -> Optional[BuildConfig]:
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
                return to_build_config(raw_config, module_name)
            except ValueError as error:
                _echo_error(
                    f"Failed to load build config for {module_name!r} - {error}"
                )
                return None
    return None


def _echo_error(msg: str) -> None:
    echo(msg, color="red")
