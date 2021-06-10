from logging.config import dictConfig
from typing import List

import typer

import idom
from idom.client import manage as manage_client

from .config import all_options
from .log import logging_config_defaults


main = typer.Typer()


@main.callback(invoke_without_command=True, no_args_is_help=True)
def root(
    version: bool = typer.Option(
        False,
        "--version",
        help="show the current version",
        show_default=False,
        is_eager=True,
    )
) -> None:
    """Command line interface for IDOM"""

    # reset logging config after Typer() has wrapped stdout
    dictConfig(logging_config_defaults())

    if version:
        typer.echo(idom.__version__)

    return None


@main.command()
def install(packages: List[str]) -> None:
    """Install a Javascript package from NPM into the client"""
    manage_client.build(packages, clean_build=False)
    return None


@main.command()
def restore() -> None:
    """Return to a fresh install of the client"""
    manage_client.restore()
    return None


@main.command()
def options() -> None:
    """Show available global options and their current values"""
    for opt in list(sorted(all_options(), key=lambda opt: opt.name)):
        name = typer.style(opt.name, bold=True)
        typer.echo(f"{name} = {opt.current}")
