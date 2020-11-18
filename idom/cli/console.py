from contextlib import contextmanager
from typing import Optional, Any, Iterator

import typer
import click_spinner

from .settings import IDOM_CLI_SHOW_SPINNER, IDOM_CLI_SHOW_OUTPUT, IDOM_CLI_DEBUG


def echo(message: str, message_color: Optional[str] = None, **kwargs: Any) -> None:
    if message_color is not None:
        message = typer.style(message, fg=getattr(typer.colors, message_color.upper()))
    if IDOM_CLI_SHOW_OUTPUT:
        typer.echo(message, **kwargs)


@contextmanager
def spinner(message: str) -> Iterator[None]:
    if not message.endswith("\n"):
        message = message + " "
    echo(message, nl=False)
    try:
        with click_spinner.spinner(
            disable=not (IDOM_CLI_SHOW_OUTPUT and IDOM_CLI_SHOW_SPINNER)
        ):
            yield None
    except Exception as error:
        echo(typer.style("✖️", fg=typer.colors.RED))
        echo(str(error), message_color="red")
        if IDOM_CLI_DEBUG:
            raise error
        else:
            raise typer.Exit(1)
    else:
        echo(typer.style("✔️", fg=typer.colors.GREEN))
