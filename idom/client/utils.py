import ast
import os
from contextlib import contextmanager
from importlib.machinery import SourceFileLoader
from pkgutil import iter_modules
from typing import Dict, Optional, List, Iterator, Any

import typer
import click_spinner


def echo(message: str, message_color: Optional[str] = None, **kwargs: Any) -> None:
    if message_color is not None:
        message = typer.style(message, fg=getattr(typer.colors, message_color.upper()))
    if _show_output():
        typer.echo(message, **kwargs)


@contextmanager
def spinner(message: str) -> Iterator[None]:
    echo(message + " ", nl=False)
    try:
        with click_spinner.spinner(disable=not _show_spinner()):
            yield None
    except Exception as error:
        echo(typer.style("✖️", fg=typer.colors.RED))
        echo(str(error), message_color="red")
        raise typer.Abort()
    else:
        echo(typer.style("✔️", fg=typer.colors.GREEN))


def find_idom_js_dependencies_from_python_packages(
    path: Optional[str] = None,
) -> Dict[str, List[str]]:
    """Find javascript dependencies declared by Python modules

    Parameters:
        path:
            Search for all importable modules under the given path. Default search
            ``sys.path`` if ``path`` is ``None``.

    Returns:
        Mapping of module names to their corresponding list of discovered dependencies.
    """
    module_depedencies: Dict[str, List[str]] = {}
    for module_info in iter_modules(path):
        module_loader = module_info.module_finder.find_module(module_info.name)
        if isinstance(module_loader, SourceFileLoader):
            module_src = module_loader.get_source(module_info.name)
            module_depedencies[module_info.name] = _get_js_dependencies_from_source(
                module_info.name, module_src
            )
    return module_depedencies


def _get_js_dependencies_from_source(module_name: str, module_src: str) -> List[str]:
    dependencies: List[str] = []
    for node in ast.parse(module_src).body:
        if isinstance(node, ast.Assign) and (
            len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "idom_js_dependencies"
        ):
            value = node.value
            if not isinstance(value, ast.List):
                echo(
                    f"package {module_name!r} declared malformed 'idom_js_dependencies' "
                    f"- expected list literal, but found {type(value).__name__} expression",
                    message_color="red",
                )
                continue
            for item in value.elts:
                if not isinstance(item, ast.Str):
                    echo(
                        f"package {module_name!r} declared malformed 'idom_js_dependencies' "
                        f"- expected string literals but found {type(item).__name__} expresion",
                        message_color="red",
                    )
                    continue
                dependencies.append(item.s)
    return dependencies


def _show_spinner() -> bool:
    return _show_output() and bool(int(os.environ.get("IDOM_SHOW_SPINNER", 1)))


def _show_output() -> bool:
    return bool(int(os.environ.get("IDOM_SHOW_CLIENT_MANAGEMENT_OUTPUT", 1)))
