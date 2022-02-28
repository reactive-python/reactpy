from __future__ import annotations

import functools
import os
import re
from pathlib import Path
from typing import Any, Callable, TypeVar

import nox
from nox.sessions import Session


ROOT = Path(__file__).parent
SRC = ROOT / "src"
POSARGS_PATTERN = re.compile(r"^(\w+)\[(.+)\]$")
TRUE_VALUES = {"true", "True", "TRUE", "1"}


_Return = TypeVar("_Return")


def do_first(
    first_session_func: Callable[[Session], None]
) -> Callable[[Callable[[Session], _Return]], Callable[[Session], _Return]]:
    """Decorator for functions defining session actions that should happen first

    >>> @do_first
    >>> def setup(session):
    >>>     ...  # do some setup
    >>>
    >>> @setup
    >>> def the_actual_session(session):
    >>>     ...  # so actual work

    This makes it quick an easy to define common setup actions.
    """

    def setup(
        second_session_func: Callable[[Session], _Return]
    ) -> Callable[[Session], _Return]:
        @functools.wraps(second_session_func)
        def wrapper(session: Session) -> Any:
            first_session_func(session)
            return second_session_func(session)

        return wrapper

    return setup


@do_first
def apply_standard_pip_upgrades(session: Session) -> None:
    session.install("--upgrade", "pip")


@do_first
def install_latest_npm_in_ci(session: Session) -> None:
    if os.environ.get("CI") in TRUE_VALUES:
        session.log("Running in CI environment - installing latest NPM")
        session.run("npm", "install", "-g", "npm@latest", external=True)


@nox.session(reuse_venv=True)
@apply_standard_pip_upgrades
def format(session: Session) -> None:
    """Auto format Python and Javascript code"""
    # format Python
    install_requirements_file(session, "check-style")
    session.run("black", ".")
    session.run("isort", ".")

    # format client Javascript
    session.chdir(SRC / "client")
    session.run("npm", "run", "format", external=True)

    # format docs Javascript
    session.chdir(ROOT / "docs" / "source" / "_custom_js")
    session.run("npm", "run", "format", external=True)


@nox.session(reuse_venv=True)
@apply_standard_pip_upgrades
def example(session: Session) -> None:
    """Run an example"""
    session.install("matplotlib")
    install_idom_dev(session)
    session.run(
        "python",
        "scripts/one_example.py",
        *session.posargs,
        env=get_idom_script_env(),
    )


@nox.session(reuse_venv=True)
@install_latest_npm_in_ci
@apply_standard_pip_upgrades
def docs(session: Session) -> None:
    """Build and display documentation in the browser (automatically reloads on change)"""
    install_requirements_file(session, "build-docs")
    install_idom_dev(session, extras="all")
    session.run(
        "python",
        "scripts/live_docs.py",
        "--open-browser",
        # watch python source too
        "--watch=src/idom",
        # for some reason this matches absolute paths
        "--ignore=**/_auto/*",
        "--ignore=**/_static/custom.js",
        "--ignore=**/node_modules/*",
        "--ignore=**/package-lock.json",
        "-a",
        "-E",
        "-b",
        "html",
        "docs/source",
        "docs/build",
        env={**os.environ, **get_idom_script_env()},
    )


@nox.session
def docs_in_docker(session: Session) -> None:
    """Build a docker image for the documentation and run it to mimic production"""
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
    session.notify("test_python", posargs=session.posargs)
    session.notify("test_docs")
    session.notify("test_javascript")


@nox.session
def test_python(session: Session) -> None:
    """Run all Python checks"""
    session.notify("test_python_suite", posargs=session.posargs)
    session.notify("test_python_types")
    session.notify("test_python_style")
    session.notify("test_python_build")


@nox.session
def test_javascript(session: Session) -> None:
    """Run all Javascript checks"""
    session.notify("test_javascript_suite")
    session.notify("test_javascript_build")
    session.notify("test_javascript_style")


@nox.session
@install_latest_npm_in_ci
@apply_standard_pip_upgrades
def test_python_suite(session: Session) -> None:
    """Run the Python-based test suite"""
    session.env["IDOM_DEBUG_MODE"] = "1"
    install_requirements_file(session, "test-env")

    posargs = session.posargs
    posargs += ["--reruns", "3", "--reruns-delay", "1"]

    if "--no-cov" in session.posargs:
        session.log("Coverage won't be checked")
        session.install(".[all]")
    else:
        posargs += ["--cov=src/idom", "--cov-report", "term"]
        install_idom_dev(session, extras="all")

    session.run("pytest", *posargs)


@nox.session
@apply_standard_pip_upgrades
def test_python_types(session: Session) -> None:
    """Perform a static type analysis of the Python codebase"""
    install_requirements_file(session, "check-types")
    install_requirements_file(session, "pkg-deps")
    install_requirements_file(session, "pkg-extras")
    session.run("mypy", "--strict", "src/idom")


@nox.session
@apply_standard_pip_upgrades
def test_python_style(session: Session) -> None:
    """Check that Python style guidelines are being followed"""
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
def test_python_build(session: Session) -> None:
    """Test whether the Python package can be build for distribution"""
    install_requirements_file(session, "build-pkg")
    session.run("python", "-m", "build", "--sdist", "--wheel", "--outdir", "dist", ".")


@nox.session
@install_latest_npm_in_ci
@apply_standard_pip_upgrades
def test_docs(session: Session) -> None:
    """Verify that the docs build and that doctests pass"""
    install_requirements_file(session, "build-docs")
    install_idom_dev(session, extras="all")
    session.run(
        "sphinx-build",
        "-a",  # re-write all output files
        "-T",  # show full tracebacks
        "-W",  # turn warnings into errors
        "--keep-going",  # complete the build, but still report warnings as errors
        "-b",
        "html",
        "docs/source",
        "docs/build",
    )
    session.run("sphinx-build", "-b", "doctest", "docs/source", "docs/build")
    # ensure docker image build works too
    session.run("docker", "build", ".", "--file", "docs/Dockerfile", external=True)


@do_first
@install_latest_npm_in_ci
def setup_client_env(session: Session) -> None:
    session.chdir(SRC / "client")
    session.run("npm", "install", external=True)


@nox.session
@setup_client_env
def test_javascript_suite(session: Session) -> None:
    """Run the Javascript-based test suite and ensure it bundles succesfully"""
    session.run("npm", "run", "test", external=True)


@nox.session
@setup_client_env
def test_javascript_build(session: Session) -> None:
    """Run the Javascript-based test suite and ensure it bundles succesfully"""
    session.run("npm", "run", "test", external=True)


@nox.session
@setup_client_env
def test_javascript_style(session: Session) -> None:
    """Check that Javascript style guidelines are being followed"""
    session.run("npm", "run", "check-format", external=True)


@nox.session
def build_js(session: Session) -> None:
    """Build javascript client code"""
    session.chdir(SRC / "client")
    session.run("npm", "run", "build", external=True)


@nox.session
def tag(session: Session) -> None:
    """Create a new git tag"""
    if len(session.posargs) > 1:
        session.error("To many arguments")

    try:
        new_version = session.posargs[0]
    except IndexError:
        session.error("No version tag given")

    install_requirements_file(session, "make-release")

    # check that version is valid semver
    session.run("pysemver", "check", new_version)

    old_version = get_version()
    session.log(f"Old version: {old_version}")
    session.log(f"New version: {new_version}")
    set_version(new_version)

    session.run("python", "scripts/update_versions.py")

    # trigger npm install to update package-lock.json
    session.install("-e", ".")

    try:
        session.run(
            "git",
            "diff",
            "--cached",
            "--exit-code",
            external=True,
        )
    except Exception:
        session.error("Cannot create a tag - there are uncommited changes")

    version = get_version()
    install_requirements_file(session, "make-release")
    session.run("pysemver", "check", version)

    changelog_file = ROOT / "docs" / "source" / "about" / "changelog.rst"
    for line in changelog_file.read_text().splitlines():
        if line == version:
            session.log(f"Found changelog section for version {version}")
            break
    else:
        session.error(
            f"No changelog entry for {version} in {changelog_file} - "
            f"make sure you have a title section called {version}."
        )

    if session.interactive:
        session.log()
        response = input("confirm (yes/no): ").lower()
        if response != "yes":
            return None

    # stage, commit, tag, and push version bump
    session.run("git", "add", "--all")
    session.run("git", "commit", "-m", repr(f"update version to {new_version}"))
    session.run("git", "tag", version, external=True)
    session.run("git", "push", "--tags", external=True)


@nox.session(reuse_venv=True)
def changes_since_release(session: Session) -> None:
    """Output the latest changes since the last release"""
    session.install("requests", "python-dateutil")
    session.run("python", "scripts/changes_since_release.py", *session.posargs)


def install_requirements_file(session: Session, name: str) -> None:
    file_path = ROOT / "requirements" / (name + ".txt")
    assert file_path.exists(), f"requirements file {file_path} does not exist"
    session.install("-r", str(file_path))


def install_idom_dev(session: Session, extras: str = "stable") -> None:
    if "--no-install" not in session.posargs:
        session.install("-e", f".[{extras}]")
    else:
        session.posargs.remove("--no-install")


def get_version() -> str:
    return (ROOT / "VERSION").read_text().strip()


def set_version(new: str) -> None:
    (ROOT / "VERSION").write_text(new.strip() + "\n")


def get_idom_script_env() -> dict[str, str]:
    return {
        "PYTHONPATH": os.getcwd(),
        "IDOM_DEBUG_MODE": os.environ.get("IDOM_DEBUG_MODE", "1"),
        "IDOM_CHECK_VDOM_SPEC": os.environ.get("IDOM_CHECK_VDOM_SPEC", "0"),
    }
