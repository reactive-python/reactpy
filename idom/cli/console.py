import os
from contextlib import contextmanager
from typing import Optional, Any, Iterator

import typer
import click_spinner


os.environ.setdefault("IDOM_CLI_SHOW_SPINNER", "1")
os.environ.setdefault("IDOM_CLI_SHOW_OUTPUT", "1")


def echo(message: str, message_color: Optional[str] = None, **kwargs: Any) -> None:
    if message_color is not None:
        message = typer.style(message, fg=getattr(typer.colors, message_color.upper()))
    if _show_output():
        typer.echo(message, **kwargs)


@contextmanager
def spinner(message: str) -> Iterator[None]:
    if not message.endswith("\n"):
        message = message + " "
    echo(message, nl=False)
    try:
        with click_spinner.spinner(disable=not _show_spinner()):
            yield None
    except Exception as error:
        echo(typer.style("✖️", fg=typer.colors.RED))
        echo(str(error), message_color="red")
        raise typer.Exit(1)
    else:
        echo(typer.style("✔️", fg=typer.colors.GREEN))


def _show_spinner() -> bool:
    return _show_output() and bool(int(os.environ["IDOM_CLI_SHOW_SPINNER"]))


def _show_output() -> bool:
    return bool(int(os.environ["IDOM_CLI_SHOW_OUTPUT"]))
