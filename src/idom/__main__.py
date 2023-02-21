import click

import idom
from idom._console.rewrite_camel_case_props import rewrite_camel_case_props
from idom._console.rewrite_keys import rewrite_keys


@click.group()
@click.version_option(idom.__version__, prog_name=idom.__name__)
def app() -> None:
    pass


app.add_command(rewrite_keys)
app.add_command(rewrite_camel_case_props)


if __name__ == "__main__":
    app()
