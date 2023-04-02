from __future__ import annotations

import json
import os
import re
from argparse import REMAINDER
from dataclasses import replace
from pathlib import Path
from shutil import rmtree
from typing import TYPE_CHECKING, Callable, NamedTuple, Sequence, cast

from noxopt import Annotated, NoxOpt, Option, Session


# --- Typing Preamble ------------------------------------------------------------------


if TYPE_CHECKING:
    # not available in typing module until Python 3.8
    # not available in typing module until Python 3.10
    from typing import Literal, Protocol, TypeAlias

    class ReleasePrepFunc(Protocol):
        def __call__(
            self, session: Session, package: PackageInfo
        ) -> Callable[[bool], None]:
            ...


LanguageName: TypeAlias = "Literal['py', 'js']"


# --- Constants ------------------------------------------------------------------------


ROOT_DIR = Path(__file__).parent.resolve()
SRC_DIR = ROOT_DIR / "src"
CLIENT_DIR = SRC_DIR / "client"
REACTPY_DIR = SRC_DIR / "reactpy"
TAG_PATTERN = re.compile(
    # start
    r"^"
    # package name
    r"(?P<name>[0-9a-zA-Z-@/]+)-"
    # package version
    r"v(?P<version>[0-9][0-9a-zA-Z-\.\+]*)"
    # end
    r"$"
)
REMAINING_ARGS = Option(nargs=REMAINDER, type=str)


# --- Session Setup --------------------------------------------------------------------


group = NoxOpt(auto_tag=True)


@group.setup
def setup_checks(session: Session) -> None:
    session.install("--upgrade", "pip")
    session.run("pip", "--version")
    session.run("npm", "--version", external=True)


@group.setup("check-javascript")
def setup_javascript_checks(session: Session) -> None:
    session.chdir(CLIENT_DIR)
    session.run("npm", "ci", external=True)


# --- Session Definitions --------------------------------------------------------------


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
    session.chdir(ROOT_DIR / "docs" / "source" / "_custom_js")
    session.run("npm", "run", "format", external=True)


@group.session
def tsc(session: Session) -> None:
    session.chdir(CLIENT_DIR)
    session.run("npx", "tsc", "-b", "-w", "packages/app", external=True)


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
    session.run("mypy", "--show-error-codes", "noxfile.py")


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


@group.session
def check_javascript_tests(session: Session) -> None:
    session.run("npm", "run", "check:tests", external=True)


@group.session
def check_javascript_format(session: Session) -> None:
    session.run("npm", "run", "check:format", external=True)


@group.session
def check_javascript_types(session: Session) -> None:
    session.run("npm", "run", "build", external=True)
    session.run("npm", "run", "check:types", external=True)


@group.session
def check_javascript_build(session: Session) -> None:
    session.run("npm", "run", "build", external=True)


@group.session
def build_javascript(session: Session) -> None:
    """Build javascript client code"""
    session.chdir(CLIENT_DIR)
    session.run("npm", "run", "build", external=True)


@group.session
def build_python(session: Session) -> None:
    """Build python package dist"""
    rmtree(str(ROOT_DIR / "build"))
    rmtree(str(ROOT_DIR / "dist"))
    install_requirements_file(session, "build-pkg")
    session.run("python", "-m", "build", "--sdist", "--wheel", "--outdir", "dist", ".")


@group.session
def publish(
    session: Session,
    publish_dry_run: Annotated[
        bool,
        Option(help="whether to test the release process"),
    ] = False,
    publish_fake_tags: Annotated[
        Sequence[str],
        Option(nargs="*", type=str, help="fake tags to use for a dry run release"),
    ] = (),
) -> None:
    packages = get_packages(session)

    release_prep: dict[LanguageName, ReleasePrepFunc] = {
        "js": prepare_javascript_release,
        "py": prepare_python_release,
    }

    if publish_fake_tags and not publish_dry_run:
        session.error("Cannot specify --publish-fake-tags without --publish-dry-run")

    parsed_tags: list[TagInfo] = []
    for tag in publish_fake_tags or get_current_tags(session):
        tag_info = parse_tag(tag)
        if tag_info is None:
            session.error(
                f"Invalid tag {tag} - must be of the form <package>-<language>-<version>"
            )
        parsed_tags.append(tag_info)  # type: ignore

    publishers: list[tuple[Path, Callable[[bool], None]]] = []
    for tag, tag_pkg, tag_ver in parsed_tags:
        if tag_pkg not in packages:
            session.error(f"Tag {tag} references package {tag_pkg} that does not exist")

        pkg_name, pkg_path, pkg_lang, pkg_ver = pkg_info = packages[tag_pkg]
        if pkg_ver != tag_ver:
            session.error(
                f"Tag {tag} references version {tag_ver} of package {tag_pkg}, "
                f"but the current version is {pkg_ver}"
            )

        session.chdir(pkg_path)
        session.log(f"Preparing {tag_pkg} for release...")
        publishers.append((pkg_path, release_prep[pkg_lang](session, pkg_info)))

    for pkg_path, publish in publishers:
        session.log(f"Publishing {pkg_path}...")
        session.chdir(pkg_path)
        publish(publish_dry_run)


# --- Utilities ------------------------------------------------------------------------


def install_requirements_file(session: Session, name: str) -> None:
    file_path = ROOT_DIR / "requirements" / (name + ".txt")
    assert file_path.exists(), f"requirements file {file_path} does not exist"
    session.install("-r", str(file_path))


def install_reactpy_dev(session: Session, extras: str = "all") -> None:
    if "--no-install" not in session.posargs:
        session.install("-e", f".[{extras}]")
    else:
        session.posargs.remove("--no-install")


def get_reactpy_script_env() -> dict[str, str]:
    return {
        "PYTHONPATH": os.getcwd(),
        "REACTPY_DEBUG_MODE": os.environ.get("REACTPY_DEBUG_MODE", "1"),
        "REACTPY_TESTING_DEFAULT_TIMEOUT": os.environ.get(
            "REACTPY_TESTING_DEFAULT_TIMEOUT", "6.0"
        ),
        "REACTPY_CHECK_VDOM_SPEC": os.environ.get("REACTPY_CHECK_VDOM_SPEC", "0"),
    }


def prepare_javascript_release(
    session: Session, package: PackageInfo
) -> Callable[[bool], None]:
    node_auth_token = session.env.get("NODE_AUTH_TOKEN")
    if node_auth_token is None:
        session.error("NODE_AUTH_TOKEN environment variable must be set")

    session.run("npm", "ci", external=True)

    def publish(dry_run: bool) -> None:
        if dry_run:
            session.run(
                "npm",
                "--workspace",
                package.name,
                "pack",
                "--dry-run",
                external=True,
            )
            return
        session.run(
            "npm",
            "--workspace",
            package.name,
            "publish",
            "--access",
            "public",
            external=True,
            env={"NODE_AUTH_TOKEN": node_auth_token},
        )

    return publish


def prepare_python_release(
    session: Session, package: PackageInfo
) -> Callable[[bool], None]:
    twine_username = session.env.get("PYPI_USERNAME")
    twine_password = session.env.get("PYPI_PASSWORD")

    if not (twine_password and twine_username):
        session.error(
            "PYPI_USERNAME and PYPI_PASSWORD environment variables must be set"
        )

    for build_dir_name in ["build", "dist"]:
        build_dir_path = Path.cwd() / build_dir_name
        if build_dir_path.exists():
            rmtree(str(build_dir_path))

    install_requirements_file(session, "build-pkg")
    session.run("python", "-m", "build", "--sdist", "--wheel", "--outdir", "dist", ".")

    def publish(dry_run: bool):
        if dry_run:
            session.run("twine", "check", "dist/*")
            return

        session.run(
            "twine",
            "upload",
            "dist/*",
            env={"TWINE_USERNAME": twine_username, "TWINE_PASSWORD": twine_password},
        )

    return publish


def get_packages(session: Session) -> dict[str, PackageInfo]:
    packages: dict[str, PackageInfo] = {
        "reactpy": PackageInfo(
            "reactpy", ROOT_DIR, "py", get_reactpy_package_version(session)
        )
    }

    # collect javascript packages
    js_package_paths: list[Path] = []
    for maybed_pkg in (CLIENT_DIR / "packages").glob("*"):
        if not (maybed_pkg / "package.json").exists():
            for nmaybe_namespaced_pkg in maybed_pkg.glob("*"):
                if (nmaybe_namespaced_pkg / "package.json").exists():
                    js_package_paths.append(nmaybe_namespaced_pkg)
        else:
            js_package_paths.append(maybed_pkg)

    # get javascript package info
    for pkg in js_package_paths:
        pkg_json_file = pkg / "package.json"  # we already know this exists

        pkg_json = json.loads(pkg_json_file.read_text())

        pkg_name = pkg_json.get("name")
        pkg_version = pkg_json.get("version")

        if pkg_version is None or pkg_name is None:
            session.log(f"Skipping - {pkg_name} has no name/version in package.json")
            continue

        if pkg_name in packages:
            session.error(f"Duplicate package name {pkg_name}")

        packages[pkg_name] = PackageInfo(pkg_name, CLIENT_DIR, "js", pkg_version)

    return packages


class PackageInfo(NamedTuple):
    name: str
    path: Path
    language: LanguageName
    version: str


def get_current_tags(session: Session) -> list[str]:
    """Get tags for the current commit"""
    # check if unstaged changes
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

    tags_per_commit: dict[str, list[str]] = {}
    for commit, tag in map(
        str.split,
        cast(
            str,
            session.run(
                "git",
                "for-each-ref",
                "--format",
                r"%(objectname) %(refname:short)",
                "refs/tags",
                silent=True,
                external=True,
            ),
        ).splitlines(),
    ):
        tags_per_commit.setdefault(commit, []).append(tag)

    current_commit = cast(
        str, session.run("git", "rev-parse", "HEAD", silent=True, external=True)
    ).strip()
    tags = tags_per_commit.get(current_commit, [])

    if not tags:
        session.error("No tags found for current commit")

    session.log(f"Found tags: {tags}")

    return tags


def parse_tag(tag: str) -> TagInfo | None:
    match = TAG_PATTERN.match(tag)
    if not match:
        return None
    return TagInfo(tag, match["name"], match["version"])


class TagInfo(NamedTuple):
    tag: str
    package: str
    version: str


def get_reactpy_package_version(session: Session) -> str:  # type: ignore[return]
    pkg_root_init_file = REACTPY_DIR / "__init__.py"
    for line in pkg_root_init_file.read_text().split("\n"):
        if line.startswith('__version__ = "') and line.endswith('"  # DO NOT MODIFY'):
            return (
                line
                # get assignment value
                .split("=", 1)[1]
                # remove "DO NOT MODIFY" comment
                .split("#", 1)[0]
                # clean up leading/trailing space
                .strip()
                # remove the quotes
                [1:-1]
            )
    session.error(f"No version found in {pkg_root_init_file}")
