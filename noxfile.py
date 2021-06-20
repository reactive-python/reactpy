from __future__ import annotations

import functools
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Callable, Tuple

import nox
from nox.sessions import Session


HERE = Path(__file__).parent
POSARGS_PATTERN = re.compile(r"^(\w+)\[(.+)\]$")


def apply_standard_pip_upgrades(
    function: Callable[[Session], Any]
) -> Callable[[Session], Any]:
    @functools.wraps(function)
    def wrapper(session: Session) -> None:
        session.install("--upgrade", "pip", "setuptools", "wheel")
        return function(session)

    return wrapper


@nox.session(reuse_venv=True)
@apply_standard_pip_upgrades
def format(session: Session) -> None:
    install_requirements_file(session, "check-style")
    session.run("black", ".")
    session.run("isort", ".")


@nox.session(reuse_venv=True)
@apply_standard_pip_upgrades
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
@apply_standard_pip_upgrades
def docs(session: Session) -> None:
    """Build and display documentation in the browser (automatically reloads on change)"""
    install_requirements_file(session, "build-docs")
    install_idom_dev(session, extras="all")
    session.run(
        "python",
        "scripts/live_docs.py",
        "--open-browser",
        # for some reason this matches absolute paths
        "--ignore=**/docs/source/auto/*",
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
        "docker",
        "build",
        ".",
        "--file",
        "docs/Dockerfile",
        "--tag",
        "idom-docs:latest",
        external=True,
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
        external=True,
    )


@nox.session
def test(session: Session) -> None:
    """Run the complete test suite"""
    session.notify("test_suite", posargs=session.posargs)
    session.notify("test_types")
    session.notify("test_style")
    session.notify("test_docs")


@nox.session
@apply_standard_pip_upgrades
def test_suite(session: Session) -> None:
    """Run the Python-based test suite"""
    session.env["IDOM_DEBUG_MODE"] = "1"
    install_requirements_file(session, "test-env")

    posargs = session.posargs
    if "--no-cov" in session.posargs:
        session.log("Coverage won't be checked")
        session.install(".[all]")
    else:
        session.log("Coverage will be checked")
        posargs += ["--cov=src/idom", "--cov-report", "term"]
        install_idom_dev(session, extras="all")

    session.run("pytest", "tests", *posargs)


@nox.session
@apply_standard_pip_upgrades
def test_types(session: Session) -> None:
    """Perform a static type analysis of the codebase"""
    install_requirements_file(session, "check-types")
    install_requirements_file(session, "pkg-deps")
    install_requirements_file(session, "pkg-extras")
    session.run("mypy", "--strict", "src/idom")


@nox.session
@apply_standard_pip_upgrades
def test_style(session: Session) -> None:
    """Check that style guidelines are being followed"""
    install_requirements_file(session, "check-style")
    session.run("flake8", "src/idom", "tests", "docs")
    black_default_exclude = r"\.eggs|\.git|\.hg|\.mypy_cache|\.nox|\.tox|\.venv|\.svn|_build|buck-out|build|dist"
    session.run(
        "black",
        ".",
        "--check",
        "--exclude",
        rf"/({black_default_exclude}|venv|node_modules)/",
    )
    session.run("isort", ".", "--check-only")


@nox.session
@apply_standard_pip_upgrades
def test_docs(session: Session) -> None:
    """Verify that the docs build and that doctests pass"""
    install_requirements_file(session, "build-docs")
    install_idom_dev(session, extras="all")
    session.run("sphinx-build", "-T", "-b", "html", "docs/source", "docs/build")
    session.run("sphinx-build", "-T", "-b", "doctest", "docs/source", "docs/build")


@nox.session
def commits_since_last_tag(session: Session) -> None:
    """A basic script for outputing changelog info"""
    rst_format = "--format=rst" in session.posargs

    latest_tag = (
        subprocess.check_output(["git", "describe", "--tags", "--abbrev=0"])
        .decode()
        .strip()
    )
    commit_references = (
        subprocess.check_output(
            ["git", "log", "--pretty=reference", f"{latest_tag}..HEAD"]
        )
        .decode()
        .strip()
        .split("\n")
    )

    def parse_commit_reference(commit_ref: str) -> Tuple[str, str, str]:
        commit_sha, remainder = commit_ref.split(" ", 1)
        commit_message, commit_date = remainder[1:-1].rsplit(", ", 1)
        return commit_sha, commit_message, commit_date

    for sha, msg, _ in map(parse_commit_reference, commit_references):
        if rst_format:
            sha_repr = f":commit:`{sha}`"
        else:
            sha_repr = sha
        print(f"- {msg} - {sha_repr}")


def install_requirements_file(session: Session, name: str) -> None:
    file_path = HERE / "requirements" / (name + ".txt")
    assert file_path.exists(), f"requirements file {file_path} does not exist"
    session.install("-r", str(file_path))


def install_idom_dev(session: Session, extras: str = "stable") -> None:
    if "--no-install" not in session.posargs:
        session.install("-e", f".[{extras}]")
    else:
        session.posargs.remove("--no-install")
