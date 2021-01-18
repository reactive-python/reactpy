from typing import List

import typer

import idom
from idom.client import manage as manage_client


main = typer.Typer()
show = typer.Typer()
main.add_typer(show, name="show", short_help="Display information about IDOM")


@main.command()
def install(packages: List[str]) -> None:
    manage_client.build(packages)
    return None


@main.command()
def restore(clean_build: bool = True) -> None:
    manage_client.build([], clean_build=clean_build)
    return None


@show.command()
def version() -> None:
    typer.echo(idom.__version__)
