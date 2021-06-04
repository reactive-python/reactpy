from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import List, Tuple

import nox
from nox.sessions import Session


HERE = Path(__file__).parent
POSARGS_PATTERN = re.compile(r"^(\w+)\[(.+)\]$")


@nox.session(reuse_venv=True)
def format(session: Session) -> None:
    install_requirements_file(session, "check-style")
    session.run("black", ".")
    session.run("isort", ".")


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
    test_suite(session)
    test_types(session)
    test_style(session)
    test_docs(session)


@nox.session
def test_suite(session: Session) -> None:
    """Run the Python-based test suite"""
    session.env["IDOM_DEBUG_MODE"] = "1"
    install_requirements_file(session, "test-env")

    pytest_args = get_posargs("pytest", session)
    if "--no-cov" in pytest_args:
        session.install(".[all]")
    else:
        install_idom_dev(session, extras="all")

    session.run("pytest", "tests", *pytest_args)


@nox.session
def test_types(session: Session) -> None:
    """Perform a static type analysis of the codebase"""
    install_requirements_file(session, "check-types")
    install_requirements_file(session, "pkg-deps")
    install_requirements_file(session, "pkg-extras")
    session.run("mypy", "--strict", "src/idom")


@nox.session
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


def install_requirements_file(session: Session, name: str) -> None:
    file_path = HERE / "requirements" / (name + ".txt")
    assert file_path.exists(), f"requirements file {file_path} does not exist"
    session.install("-r", str(file_path))


def install_idom_dev(session: Session, extras: str = "stable") -> None:
    session.install("-e", f".[{extras}]")
    if "--no-restore" not in session.posargs:
        session.run("idom", "restore")
    else:
        session.posargs.remove("--no-restore")
