from typing import List

import typer

import idom
from idom.client import manage as manage_client

main = typer.Typer()
show = typer.Typer()
main.add_typer(show, name="show", short_help="Display information about IDOM")


@main.command()
def install(packages: List[str]) -> None:
    """Install a Javascript package from NPM"""
    manage_client.build(packages)
    return None


@main.command()
def restore(clean_build: bool = True) -> None:
    """Return to a fresh install of IDOM's client"""
    manage_client.restore()
    return None


@show.command()
def version() -> None:
    """The version of IDOM"""
    typer.echo(idom.__version__)
