import click

import idom
from idom._console.rewrite_keys import rewrite_keys


@click.group()
@click.version_option(idom.__version__, prog_name=idom.__name__)
def app() -> None:
    pass


app.add_command(rewrite_keys)


if __name__ == "__main__":
    app()
