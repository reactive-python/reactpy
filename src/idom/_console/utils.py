import click


def error(text: str) -> None:
    click.echo(f"{click.style('Error', fg='red')}: {text}")
