from pathlib import Path

import typer

import idom
from idom.client import manage as manage_client
from idom.client.build_config import find_build_config_item_in_python_source


main = typer.Typer()
show = typer.Typer()
main.add_typer(show, name="show", short_help="Display information about IDOM")


@main.command()
def build(entrypoint: str) -> None:
    """Configure and build the client"""
    if entrypoint.endswith(".py"):
        config = find_build_config_item_in_python_source(
            "__main__", Path.cwd() / entrypoint
        )
        if config is None:
            typer.echo(f"No build config found in {entrypoint!r}")
            manage_client.build()
        else:
            manage_client.build([config])
    else:
        typer.echo(f"Expected a '.py' file extension, not {entrypoint!r}")
        raise typer.Exit(1)


@main.command()
def restore():
    """Reset the client to its original state"""
    manage_client.restore()


@show.command()
def config() -> None:
    """Show the state of IDOM's build config"""
    typer.echo(manage_client.BUILD_CONFIG_FILE.show())
    return None


@show.command()
def version() -> None:
    typer.echo(idom.__version__)
