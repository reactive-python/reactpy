import json
from pathlib import Path
from typing import Optional

import typer

import idom
from idom.client import manage as manage_client
from idom.client.build_config import to_build_config
from idom.client.build_config import find_build_config_in_python_source


main = typer.Typer()
show = typer.Typer()
main.add_typer(show, name="show", short_help="Display information about IDOM")


@main.command()
def build(entrypoint: Optional[str] = None, build_config: Optional[str] = None) -> None:
    """Configure and build the client"""
    if build_config is not None:
        with (Path.cwd() / build_config).open() as f:
            config = to_build_config(json.load(f))
    elif entrypoint is not None:
        config = find_build_config_in_python_source("__main__", Path.cwd() / entrypoint)
        if config is None:
            typer.echo(f"No build config found in {entrypoint!r}")
    else:
        config = None
    manage_client.build(config)


@main.command()
def restore():
    """Reset the client to its original state"""
    manage_client.restore()


@show.command()
def config() -> None:
    """Show the state of IDOM's build config"""
    typer.echo(
        json.dumps(
            {
                name: conf._asdict()
                for name, conf in manage_client.build_configs().items()
            },
            indent=2,
        )
    )
    return None


@show.command()
def version() -> None:
    typer.echo(idom.__version__)
