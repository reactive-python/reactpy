"""Entry point for the ReactPy CLI."""

import click

import reactpy
from reactpy._console.rewrite_props import rewrite_props


@click.group()
@click.version_option(version=reactpy.__version__, prog_name=reactpy.__name__)
def entry_point() -> None:
    pass


entry_point.add_command(rewrite_props)


if __name__ == "__main__":
    entry_point()
