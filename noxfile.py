import os
from typing import Iterable

import nox
from nox.sessions import Session


HEADLESS = bool(int(os.environ.get("HEADLESS", "0")))
BLACK_DEFAULT_EXCLUDE = r"\.eggs|\.git|\.hg|\.mypy_cache|\.nox|\.tox|\.venv|\.svn|_build|buck-out|build|dist"


@nox.session
def test_without_coverage(session: Session) -> None:
    _test_setup(session)
    session.install(".[all]")
    _test_run(session, extra_args=["--no-cov"])


@nox.session
def test_with_coverage(session: Session) -> None:
    _test_setup(session)
    session.install("-e", ".[all]")  # coverage requires a dev install
    _test_run(session)


@nox.session
def check_types(session: Session) -> None:
    session.install("-r", "requirements/check-types.txt")
    session.install(".[all]")
    session.run("mypy", "--strict", "idom")


@nox.session
def check_style(session: Session) -> None:
    session.install("-r", "requirements/check-style.txt")
    session.run(
        "black",
        ".",
        "--check",
        "--exclude",
        rf"/({BLACK_DEFAULT_EXCLUDE}|node_modules)/",
    )
    session.run("flake8", "idom", "tests", "docs")


@nox.session
def build_docs(session: Session) -> None:
    session.install("-r", "requirements/build-docs.txt")
    session.install("-e", ".[all]")
    session.run("sphinx-build", "-b", "html", "docs/source", "docs/build")
    session.run("sphinx-build", "-b", "doctest", "docs/source", "docs/build")


def _test_setup(session: Session) -> None:
    session.env.update(os.environ)
    session.install("-r", "requirements/test-env.txt")


def _test_run(session: Session, extra_args: Iterable[str] = ()) -> None:
    args = ["pytest", "tests"]
    if HEADLESS:
        args.append("--headless")
    args.extend(extra_args)
    session.run(*args)
