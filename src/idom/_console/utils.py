import click


def echo_error(text: str) -> None:
    click.echo(f"{click.style('Error', fg='red')}: {text}")


def echo_warning(text: str) -> None:
    click.echo(f"{click.style('Warning', fg='yellow')}: {text}")
