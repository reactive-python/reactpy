from logging.config import dictConfig
from typing import List

import typer
from rich.console import Console
from rich.table import Table

import idom
from idom.client import _private
from idom.client import manage as manage_client

from .log import logging_config_defaults


main = typer.Typer()
console = Console()


@main.callback()
def init() -> None:
    # reset logging config after Typer() has wrapped stdout
    dictConfig(logging_config_defaults())


@main.command()
def install(packages: List[str]) -> None:
    """Install a Javascript package from NPM into the client"""
    manage_client.build(packages, clean_build=False)
    return None


@main.command()
def restore() -> None:
    """Return to a fresh install of Ithe client"""
    manage_client.restore()
    return None


@main.command()
def version(verbose: bool = False) -> None:
    """Show version information"""
    if not verbose:
        console.print(idom.__version__)
    else:
        table = Table()

        table.add_column("Package")
        table.add_column("Version")
        table.add_column("Language")

        table.add_row("idom", str(idom.__version__), "Python")

        for js_pkg, js_ver in _private.build_dependencies().items():
            table.add_row(js_pkg, js_ver, "Javascript")

        console.print(table)
