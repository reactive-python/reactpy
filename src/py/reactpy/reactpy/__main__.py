import click

import reactpy
from reactpy._console.rewrite_camel_case_props import rewrite_camel_case_props
from reactpy._console.rewrite_keys import rewrite_keys


@click.group()
@click.version_option(reactpy.__version__, prog_name=reactpy.__name__)
def app() -> None:
    pass


app.add_command(rewrite_keys)
app.add_command(rewrite_camel_case_props)


if __name__ == "__main__":
    app()
