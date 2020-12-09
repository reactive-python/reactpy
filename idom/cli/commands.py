import os
import json
from pathlib import Path
from typing import Optional, List

import typer

import idom
from idom.client import manage as manage_client
from idom.client.build_config import find_build_config_entry_in_python_file

from . import settings
from .console import echo


main = typer.Typer()
show = typer.Typer()
main.add_typer(show, name="show", short_help="Display information about IDOM")


@main.command()
def install(packages: List[str]):
    config = manage_client.build_config()
    with config.change_entry("__main__") as entry:
        entry_packages = entry.setdefault("js_dependencies", [])
        entry_packages.extend(
            [
                pkg
                for pkg in packages
                if not config.entry_has_dependency("__main__", pkg)
            ]
        )
    manage_client.build()


@main.command()
def build(
    entrypoint: Optional[str] = typer.Option(
        None,
        "--entrypoint",
        "-e",
        help="A python file containing a build config",
    ),
    restore: bool = typer.Option(
        None,
        "--restore",
        "-r",
        help="Restore the client build",
    ),
) -> None:
    """Configure and build the client"""
    if restore and entrypoint:
        echo(
            "--restore and --entrypoint are mutually exclusive options",
            message_color="red",
        )
        raise typer.Exit(1)

    if restore:
        manage_client.restore()
        return None

    if entrypoint is None:
        manage_client.build()
        return None

    config = find_build_config_entry_in_python_file("__main__", Path.cwd() / entrypoint)
    if config is None:
        echo(f"No build config found in {entrypoint!r}")
        manage_client.build()
    else:
        manage_client.build([config])


@show.command()
def build_config() -> None:
    """Show the state of IDOM's build config"""
    echo(json.dumps(manage_client.build_config().data, indent=2))
    return None


@show.command()
def version() -> None:
    echo(idom.__version__)


@show.command()
def environment() -> None:
    for n in settings.NAMES:
        echo(f"{n}={os.environ[n]}")
