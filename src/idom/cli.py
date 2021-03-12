from typing import List

import typer
from rich.console import Console
from rich.table import Table

import idom
from idom.client import manage as manage_client


main = typer.Typer()
console = Console()

# --- Subcommands ---
client = typer.Typer(name="client", short_help="Manage IDOM's built-in client")
show = typer.Typer(name="show", short_help="Display information about IDOM")
main.add_typer(client)
main.add_typer(show)


@client.command()
def install(packages: List[str]) -> None:
    """Install a Javascript package from NPM into the client"""
    manage_client.build(packages, clean_build=False)
    return None


@client.command()
def rebuild(clean: bool = False) -> None:
    """Rebuild the client (keeps currently installed packages by default)"""
    manage_client.build([], clean_build=clean)


@client.command()
def restore() -> None:
    """Return to a fresh install of Ithe client"""
    manage_client.restore()
    return None


@show.command()
def version(verbose: bool = False) -> None:
    """Show version information"""
    if not verbose:
        console.print(idom.__version__)
    else:
        table = Table()

        table.add_column("Package")
        table.add_column("Version")
        table.add_column("Language")

        table.add_row("idom", str(idom.__version__), "Python")

        for js_pkg, js_ver in manage_client.dependency_versions().items():
            table.add_row(js_pkg, js_ver, "Javascript")

        console.print(table)
