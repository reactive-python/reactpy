import json
from pathlib import Path
from typing import Optional

import typer
from idom.client import manage as manage_client
from idom.client.build_config import to_build_config
from idom.client.build_config import find_build_config_in_python_source


cli = typer.Typer()


@cli.command()
def build(entrypoint: Optional[str] = None, build_config: Optional[str] = None) -> None:
    """Install javascript packages with NPM"""
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


@cli.command()
def show_config() -> None:
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


@cli.command()
def restore():
    manage_client.restore()


if __name__ == "__main__":  # pragma: no cover
    cli()
