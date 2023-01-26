import click

from idom import __version__
from idom._console.update_html_usages import update_html_usages


app = click.Group(
    commands=[
        update_html_usages,
    ]
)

if __name__ == "__main__":
    app()
