import sys
import argparse
from typing import TypeVar, Callable, Any, DefaultDict, Dict

from idom.client.manage import install, delete_web_modules, installed, restore


_Func = TypeVar("_Func", bound=Callable[..., Any])


def main(*args: str) -> None:
    cli = argparse.ArgumentParser()
    cli.add_argument(
        "command", choices=["install", "uninstall", "installed", "restore"]
    )
    cli.add_argument(
        "dependencies",
        nargs="*",
        type=str,
    )
    cli.add_argument(
        "--exports",
        nargs="*",
        type=str,
        default=None,
    )
    cli.add_argument("--force", action="store_true")
    cli.add_argument("--debug", action="store_true")

    parsed = cli.parse_args(args or sys.argv[1:])

    try:
        return run(parsed)
    except Exception as error:
        if parsed.debug:
            raise
        print(f"{type(error).__name__}: {error}")
        sys.exit(1)


ARG_REQUIREMENTS: Dict[str, Dict[str, Any]] = {
    "installed restore uninstall": {"exports": None, "force": False},
    "installed restore": {"dependencies": []},
}


def run(args: argparse.Namespace) -> None:
    requirements: DefaultDict[str, Dict[str, Any]] = DefaultDict(dict)
    for cmd, reqs in ARG_REQUIREMENTS.items():
        for c in cmd.split():
            requirements[c].update(reqs)

    for k, v in requirements.get(args.command, {}).items():
        if getattr(args, k) != v:
            raise ValueError(
                f"{args.command!r} does not support {k}={getattr(args, k)}"
            )

    if args.command == "install":
        install(args.dependencies or [], args.exports or [], args.force)
    elif args.command == "uninstall":
        delete_web_modules(args.dependencies)
    elif args.command == "restore":
        restore()
    else:
        print("Installed:")
        for name in installed():
            print("-", name)


if __name__ == "__main__":  # pragma: no cover
    main()
