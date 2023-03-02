from __future__ import annotations

import os
from argparse import REMAINDER
from dataclasses import replace
from pathlib import Path
from shutil import rmtree
from typing import Sequence

from noxopt import Annotated, NoxOpt, Option, Session


ROOT = Path(__file__).parent
CLIENT_DIR = ROOT / "src" / "client"

REMAINING_ARGS = Option(nargs=REMAINDER, type=str)

group = NoxOpt(auto_tag=True)


@group.setup
def setup_checks(
    session: Session,
    ci: Annotated[bool, Option(help="whether running in CI")] = False,
) -> None:
    session.install("--upgrade", "pip")
    if ci:
        session.log("Running in CI environment - installing latest NPM")
        session.run("npm", "install", "-g", "npm@latest", external=True)


@group.session
def format(session: Session) -> None:
    """Auto format Python and Javascript code"""
    # format Python
    install_requirements_file(session, "check-style")
    session.run("black", ".")
    session.run("isort", ".")

    # format client Javascript
    session.chdir(CLIENT_DIR)
    session.run("npm", "run", "format", external=True)

    # format docs Javascript
    session.chdir(ROOT / "docs" / "source" / "_custom_js")
    session.run("npm", "run", "format", external=True)


@group.session
def example(session: Session) -> None:
    """Run an example"""
    session.install("matplotlib")
    install_reactpy_dev(session)
    session.run(
        "python",
        "scripts/one_example.py",
        *session.posargs,
        env=get_reactpy_script_env(),
    )


@group.session
def docs(session: Session) -> None:
    """Build and display documentation in the browser (automatically reloads on change)"""
    install_requirements_file(session, "build-docs")
    install_reactpy_dev(session)
    session.run(
        "python",
        "scripts/live_docs.py",
        "--open-browser",
        # watch python source too
        "--watch=src/reactpy",
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
        env={**os.environ, **get_reactpy_script_env()},
    )


@group.session
def docs_in_docker(session: Session) -> None:
    """Build a docker image for the documentation and run it to mimic production"""
    session.run(
        "docker",
        "build",
        ".",
        "--file",
        "docs/Dockerfile",
        "--tag",
        "reactpy-docs:latest",
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
        "reactpy-docs:latest",
        external=True,
    )


@group.session
def check_python_tests(
    session: Session,
    no_cov: Annotated[bool, Option(help="turn off coverage checks")] = False,
    headed: Annotated[bool, Option(help="run tests with a headed browser")] = False,
    pytest: Annotated[Sequence[str], replace(REMAINING_ARGS, help="pytest args")] = (),
) -> None:
    """Run the Python-based test suite"""
    session.env["REACTPY_DEBUG_MODE"] = "1"
    install_requirements_file(session, "test-env")
    session.run("playwright", "install", "chromium")

    args = ["pytest", *pytest]
    if headed:
        args.append("--headed")

    if no_cov:
        session.log("Coverage won't be checked")
        session.install(".[all]")
    else:
        args = ["coverage", "run", "--source=src/reactpy", "--module", *args]
        install_reactpy_dev(session)

    session.run(*args)

    if not no_cov:
        session.run("coverage", "report")


@group.session
def check_python_types(session: Session) -> None:
    """Perform a static type analysis of the Python codebase"""
    install_requirements_file(session, "check-types")
    install_requirements_file(session, "pkg-deps")
    install_requirements_file(session, "pkg-extras")
    session.run("mypy", "--version")
    session.run("mypy", "--show-error-codes", "--strict", "src/reactpy")


@group.session
def check_python_format(session: Session) -> None:
    """Check that Python style guidelines are being followed"""
    install_requirements_file(session, "check-style")
    session.run("flake8", "src/reactpy", "tests", "docs")
    session.run("black", ".", "--check")
    session.run("isort", ".", "--check-only")


@group.session
def check_python_build(session: Session) -> None:
    """Test whether the Python package can be build for distribution"""
    install_requirements_file(session, "build-pkg")
    session.run("python", "-m", "build", "--sdist", "--wheel", "--outdir", "dist", ".")


@group.session
def check_docs(session: Session) -> None:
    """Verify that the docs build and that doctests pass"""
    install_requirements_file(session, "build-docs")
    install_reactpy_dev(session)
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


@group.setup("check-javascript")
def setup_javascript_checks(session: Session) -> None:
    session.chdir(CLIENT_DIR)
    session.run("npm", "install", external=True)


@group.session
def check_javascript_suite(session: Session) -> None:
    """Run the Javascript-based test suite and ensure it bundles succesfully"""
    session.run("npm", "run", "test", external=True)


@group.session
def check_javascript_build(session: Session) -> None:
    """Run the Javascript-based test suite and ensure it bundles succesfully"""
    session.run("npm", "run", "test", external=True)


@group.session
def check_javascript_format(session: Session) -> None:
    """Check that Javascript style guidelines are being followed"""
    session.run("npm", "run", "check-format", external=True)


@group.session
def build_javascript(session: Session) -> None:
    """Build javascript client code"""
    session.chdir(CLIENT_DIR)
    session.run("npm", "run", "build", external=True)


@group.session
def build_python(session: Session) -> None:
    """Build javascript client code"""
    rmtree(str(ROOT / "build"))
    rmtree(str(ROOT / "dist"))
    session.install("build", "wheel")
    session.run("python", "-m", "build", "--sdist", "--wheel", "--outdir", "dist", ".")


@group.session
def tag(session: Session, version: str = "") -> None:
    """Create a new git tag"""
    try:
        session.run(
            "git",
            "diff",
            "--cached",
            "--exit-code",
            silent=True,
            external=True,
        )
        session.run(
            "git",
            "diff",
            "--exit-code",
            silent=True,
            external=True,
        )
    except Exception:
        session.error("Cannot create a tag - there are uncommited changes")

    if not version:
        session.error("No version tag given")
    new_version = version

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

    version = get_version()
    install_requirements_file(session, "make-release")
    session.run("pysemver", "check", version)

    changelog_file = ROOT / "docs" / "source" / "about" / "changelog.rst"
    for line in changelog_file.read_text().splitlines():
        if line == f"v{version}":
            session.log(f"Found changelog section for version {version}")
            break
    else:
        session.error(
            f"Something went wrong - could not find a title section for {version}"
        )

    if session.interactive:
        response = input("Confirm (yes/no): ").lower()
        if response != "yes":
            session.error("Did not create tag")

    # stage, commit, tag, and push version bump
    session.run("git", "add", "--all", external=True)
    session.run("git", "commit", "-m", f"version {new_version}", external=True)
    session.run("git", "tag", version, external=True)
    session.run("git", "push", "origin", "main", "--tags", external=True)


@group.session
def changes_since_release(session: Session) -> None:
    """Output the latest changes since the last release"""
    session.install("requests", "python-dateutil")
    session.run("python", "scripts/changes_since_release.py", *session.posargs)


def install_requirements_file(session: Session, name: str) -> None:
    file_path = ROOT / "requirements" / (name + ".txt")
    assert file_path.exists(), f"requirements file {file_path} does not exist"
    session.install("-r", str(file_path))


def install_reactpy_dev(session: Session, extras: str = "all") -> None:
    session.run("pip", "--version")
    if "--no-install" not in session.posargs:
        session.install("-e", f".[{extras}]")
    else:
        session.posargs.remove("--no-install")


def get_version() -> str:
    return (ROOT / "VERSION").read_text().strip()


def set_version(new: str) -> None:
    (ROOT / "VERSION").write_text(new.strip() + "\n")


def get_reactpy_script_env() -> dict[str, str]:
    return {
        "PYTHONPATH": os.getcwd(),
        "REACTPY_DEBUG_MODE": os.environ.get("REACTPY_DEBUG_MODE", "1"),
        "REACTPY_TESTING_DEFAULT_TIMEOUT": os.environ.get(
            "REACTPY_TESTING_DEFAULT_TIMEOUT", "6.0"
        ),
        "REACTPY_CHECK_VDOM_SPEC": os.environ.get("REACTPY_CHECK_VDOM_SPEC", "0"),
    }
