import os
import re
from pathlib import Path
from typing import List

import nox
from nox.sessions import Session


HERE = Path(__file__).parent
POSARGS_PATTERN = re.compile(r"^(\w+)\[(.+)\]$")


def get_posargs(name: str, session: Session) -> List[str]:
    """Find named positional arguments

    Positional args of the form `name[arg1,arg2]` will be parsed as ['arg1', 'arg2'] if
    the given `name` matches. Any args not matching that pattern will be added to the
    list of args as well. Thus the following:

    --param session_1[arg1,arg2] session_2[arg3,arg4]

    where `name` is session_1 would produce ['--param', 'arg1', 'arg2']
    """
    collected_args: List[str] = []
    for arg in session.posargs:
        match = POSARGS_PATTERN.match(arg)
        if match is not None:
            found_name, found_args = match.groups()
            if name == found_name:
                collected_args.extend(map(str.strip, found_args.split(",")))
        else:
            collected_args.append(arg)
    return collected_args


@nox.session(reuse_venv=True)
def example(session: Session) -> None:
    """Run an example"""
    if not session.posargs:
        print("No example name given. Choose from:")
        for found_example_file in (HERE / "docs" / "source" / "examples").glob("*.py"):
            print("-", found_example_file.stem)
        return None

    session.install("matplotlib")
    install_idom_dev(session)
    session.run("python", "scripts/one_example.py", *session.posargs)


@nox.session(reuse_venv=True)
def docs(session: Session) -> None:
    """Build and display documentation in the browser (automatically reloads on change)"""
    session.install("-r", "requirements/build-docs.txt")
    install_idom_dev(session, extras="all")
    session.run(
        "python",
        "scripts/live_docs.py",
        "--open-browser",
        "--ignore=build/**/*",
        "-a",
        "-E",
        "-b",
        "html",
        "docs/source",
        "docs/build",
        env={"PYTHONPATH": os.getcwd()},
    )


@nox.session
def docs_in_docker(session: Session) -> None:
    session.run(
        "docker", "build", ".", "--file", "docs/Dockerfile", "--tag", "idom-docs:latest"
    )
    session.run(
        "docker",
        "run",
        "-it",
        "-p",
        "5000:5000",
        "-e",
        "DEBUG=1",
        "--rm",
        "idom-docs:latest",
    )


@nox.session
def test(session: Session) -> None:
    """Run the complete test suite"""
    session.install("--upgrade", "pip", "setuptools", "wheel")
    test_python(session)
    test_types(session)
    test_style(session)
    test_docs(session)


@nox.session
def test_python(session: Session) -> None:
    """Run the Python-based test suite"""
    session.env["IDOM_DEBUG_MODE"] = "1"
    session.install("-r", "requirements/test-env.txt")

    pytest_args = get_posargs("pytest", session)
    if "--no-cov" in pytest_args:
        session.install(".[all]")
    else:
        install_idom_dev(session, extras="all")

    session.run("pytest", "tests", *pytest_args)


@nox.session
def test_types(session: Session) -> None:
    """Perform a static type analysis of the codebase"""
    session.install("-r", "requirements/check-types.txt")
    session.install("-r", "requirements/pkg-deps.txt")
    session.install("-r", "requirements/pkg-extras.txt")
    session.run("mypy", "--strict", "src/idom")


@nox.session
def test_style(session: Session) -> None:
    """Check that style guidelines are being followed"""
    session.install("-r", "requirements/check-style.txt")
    session.run("flake8", "src/idom", "tests", "docs")
    black_default_exclude = r"\.eggs|\.git|\.hg|\.mypy_cache|\.nox|\.tox|\.venv|\.svn|_build|buck-out|build|dist"
    session.run(
        "black",
        ".",
        "--check",
        "--exclude",
        rf"/({black_default_exclude}|node_modules)/",
    )
    session.run("isort", ".", "--check-only")


@nox.session
def test_docs(session: Session) -> None:
    """Verify that the docs build and that doctests pass"""
    session.install("-r", "requirements/build-docs.txt")
    install_idom_dev(session, extras="all")
    session.run("sphinx-build", "-b", "html", "docs/source", "docs/build")
    session.run("sphinx-build", "-b", "doctest", "docs/source", "docs/build")


def install_idom_dev(session: Session, extras: str = "stable") -> None:
    session.install("-e", f".[{extras}]")
    if "--no-restore" not in session.posargs:
        session.run("idom", "client", "restore")
