import json
from pathlib import Path
from typing import Optional

import typer

import idom
from idom.client import manage as manage_client
from idom.client.build_config import find_build_config_item_in_python_file

from . import settings


main = typer.Typer()
show = typer.Typer()
main.add_typer(show, name="show", short_help="Display information about IDOM")


@main.command()
def build(
    entrypoint: Optional[str] = typer.Option(
        None,
        "--entrypoint",
        "-e",
        help="A python file containing a build config",
    ),
) -> None:
    """Configure and build the client"""
    if entrypoint is None:
        manage_client.build()
        return None

    config = find_build_config_item_in_python_file("__main__", Path.cwd() / entrypoint)
    if config is None:
        typer.echo(f"No build config found in {entrypoint!r}")
        manage_client.build()
    else:
        manage_client.build([config])


@main.command()
def restore():
    """Reset the client to its original state"""
    manage_client.restore()


@show.command()
def build_config() -> None:
    """Show the state of IDOM's build config"""
    typer.echo(json.dumps(manage_client.build_config().config, indent=2))
    return None


@show.command()
def version() -> None:
    typer.echo(idom.__version__)


@show.command()
def environment() -> None:
    for n in settings.NAMES:
        typer.echo(f"{n}={getattr(settings, n)}")
