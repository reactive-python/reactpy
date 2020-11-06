from typing import List

import typer
from idom.client import manage as manage_client


cli = typer.Typer()


@cli.command()
def build():
    manage_client.install([])


@cli.command()
def install(packages: List[str]) -> None:
    """Install javascript packages with NPM"""
    manage_client.install(
        list(packages or [])  # BUG: https://github.com/tiangolo/typer/issues/127
    )


@cli.command()
def uninstall(packages: List[str], skip_missing: bool = False) -> None:
    """Uninstall javascript packages"""
    manage_client.uninstall(
        list(packages),  # BUG: https://github.com/tiangolo/typer/issues/127
        skip_missing=skip_missing,
    )


@cli.command()
def installed():
    """Print the list of installed packages"""
    typer.echo(manage_client.installed())


@cli.command()
def restore():
    manage_client.restore()


if __name__ == "__main__":  # pragma: no cover
    cli()
