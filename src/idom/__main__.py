import click

import idom
from idom._console.update_html_usages import update_html_usages


@click.group()
@click.version_option(idom.__version__, prog_name=idom.__name__)
def app() -> None:
    pass


app.add_command(update_html_usages)


if __name__ == "__main__":
    app()
