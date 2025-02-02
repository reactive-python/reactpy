"""Entry point for the ReactPy CLI."""

import click

from reactpy._console.rewrite_props import rewrite_props


@click.group()
@click.version_option(package_name="reactpy")
def entry_point() -> None:
    pass


entry_point.add_command(rewrite_props)


if __name__ == "__main__":
    entry_point()
