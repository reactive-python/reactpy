from __future__ import annotations

import json
import logging
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from shutil import rmtree
from typing import TYPE_CHECKING, Any, Callable

import semver
import toml
from invoke import task
from invoke.context import Context
from invoke.exceptions import Exit

# --- Typing Preamble ------------------------------------------------------------------


if TYPE_CHECKING:
    # not available in typing module until Python 3.8
    # not available in typing module until Python 3.10
    from typing import Literal, Protocol, TypeAlias

    class ReleasePrepFunc(Protocol):
        def __call__(
            self, context: Context, package: PackageInfo
        ) -> Callable[[bool], None]:
            ...

    LanguageName: TypeAlias = "Literal['py', 'js']"


# --- Constants ------------------------------------------------------------------------


log = logging.getLogger(__name__)
log.setLevel("INFO")
log_handler = logging.StreamHandler(sys.stdout)
log_handler.setFormatter(logging.Formatter("%(message)s"))
log.addHandler(log_handler)


# --- Constants ------------------------------------------------------------------------


ROOT = Path(__file__).parent
SRC_DIR = ROOT / "src"
JS_DIR = SRC_DIR / "js"
PY_DIR = SRC_DIR / "py"
PY_PROJECTS = [p for p in PY_DIR.iterdir() if (p / "pyproject.toml").exists()]
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


# --- Tasks ----------------------------------------------------------------------------


@task
def env(context: Context):
    """Install development environment"""
    env_py(context)
    env_js(context)


@task
def env_py(context: Context):
    """Install Python development environment"""
    for py_proj in PY_PROJECTS:
        py_proj_toml = toml.load(py_proj / "pyproject.toml")
        hatch_default_env = py_proj_toml["tool"]["hatch"]["envs"].get("default", {})
        hatch_default_features = hatch_default_env.get("features", [])
        hatch_default_deps = hatch_default_env.get("dependencies", [])
        with context.cd(py_proj):
            context.run(f"pip install '.[{','.join(hatch_default_features)}]'")
        context.run(f"pip install {' '.join(map(repr, hatch_default_deps))}")


@task
def env_js(context: Context):
    """Install JS development environment"""
    in_js(
        context,
        "npm ci",
        "npm run build",
        hide="out",
    )


@task
def lint_py(context: Context, fix: bool = False):
    """Run linters and type checkers"""
    if fix:
        context.run("ruff --fix .")
    else:
        context.run("ruff .")
        context.run("black --check --diff .")
        in_py(
            context,
            f"flake8 --toml-config {ROOT / 'pyproject.toml'} .",
            "hatch run lint:all",
        )


@task(pre=[env_js])
def lint_js(context: Context, fix: bool = False):
    """Run linters and type checkers"""
    if fix:
        in_js(context, "npm run fix:format")
    else:
        in_js(context, "npm run check:format")
    in_js(context, "npm run check:types")


@task
def test_py(context: Context, no_cov: bool = False):
    """Run test suites"""
    in_py(context, f"hatch run {'test' if no_cov else 'cov'} --maxfail=3")


@task(pre=[env_js])
def test_js(context: Context):
    """Run test suites"""
    in_js(context, "npm run check:tests")


@task(pre=[env_py])
def test_docs(context: Context):
    raise Exit("Not implemented")


@task
def publish(context: Context, dry_run: str = ""):
    """Publish packages that have been tagged for release in the current commit

    To perform a test run use `--dry-run=<name>-v<version>` to specify a comma-separated
    list of tags to simulate a release of. For example, to simulate a release of
    `@foo/bar-v1.2.3` and `baz-v4.5.6` use `--dry-run=@foo/bar-v1.2.3,baz-v4.5.6`.
    """
    packages = get_packages(context)

    release_prep: dict[LanguageName, ReleasePrepFunc] = {
        "js": prepare_js_release,
        "py": prepare_py_release,
    }

    parsed_tags: list[TagInfo] = [
        parse_tag(tag) for tag in dry_run.split(",") or get_current_tags(context)
    ]

    publishers: list[Callable[[bool], None]] = []
    for tag_info in parsed_tags:
        if tag_info.name not in packages:
            msg = f"Tag {tag_info.tag} references package {tag_info.name} that does not exist"
            raise Exit(msg)

        pkg_info = packages[tag_info.name]
        if pkg_info.version != tag_info.version:
            msg = f"Tag {tag_info.tag} references version {tag_info.version} of package {tag_info.name}, but the current version is {pkg_info.version}"
            raise Exit(msg)

        log.info(f"Preparing {tag_info.name} for release...")
        publishers.append(release_prep[pkg_info.language](context, pkg_info))

    for publish in publishers:
        publish(bool(dry_run))


# --- Utilities ------------------------------------------------------------------------


def in_py(context: Context, *commands: str, **kwargs: Any) -> None:
    for p in PY_PROJECTS:
        with context.cd(p):
            log.info(f"Running commands in {p}...")
            for c in commands:
                context.run(c, **kwargs)


def in_js(context: Context, *commands: str, **kwargs: Any) -> None:
    with context.cd(JS_DIR):
        for c in commands:
            context.run(c, **kwargs)


def get_packages(context: Context) -> dict[str, PackageInfo]:
    packages: list[PackageInfo] = []

    for maybe_pkg in PY_DIR.glob("*"):
        if (maybe_pkg / "pyproject.toml").exists():
            packages.append(make_py_pkg_info(context, maybe_pkg))
        else:
            msg = f"unexpected dir or file: {maybe_pkg}"
            raise Exit(msg)

    packages_dir = JS_DIR / "packages"
    for maybe_pkg in packages_dir.glob("*"):
        if (maybe_pkg / "package.json").exists():
            packages.append(make_js_pkg_info(maybe_pkg))
        elif maybe_pkg.is_dir():
            for maybe_ns_pkg in maybe_pkg.glob("*"):
                if (maybe_ns_pkg / "package.json").exists():
                    packages.append(make_js_pkg_info(maybe_ns_pkg))
        else:
            msg = f"unexpected dir or file: {maybe_pkg}"
            raise Exit(msg)

    packages_by_name = {p.name: p for p in packages}
    if len(packages_by_name) != len(packages):
        raise Exit("duplicate package names detected")

    return packages_by_name


def make_py_pkg_info(context: Context, pkg_dir: Path) -> PackageInfo:
    with context.cd(pkg_dir):
        proj_metadata = json.loads(context.run("hatch project metadata").stdout)
    return PackageInfo(
        name=proj_metadata["name"],
        path=pkg_dir,
        language="py",
        version=proj_metadata["version"],
    )


def make_js_pkg_info(pkg_dir: Path) -> PackageInfo:
    with (pkg_dir / "package.json").open() as f:
        pkg_json = json.load(f)
    return PackageInfo(
        name=pkg_json["name"],
        path=pkg_dir,
        language="js",
        version=pkg_json["version"],
    )


@dataclass
class PackageInfo:
    name: str
    path: Path
    language: LanguageName
    version: str


def get_current_tags(context: Context) -> set[str]:
    """Get tags for the current commit"""
    # check if unstaged changes
    try:
        context.run("git diff --cached --exit-code", hide=True)
        context.run("git diff --exit-code", hide=True)
    except Exception:
        log.error("Cannot create a tag - there are uncommited changes")
        return set()

    tags_per_commit: dict[str, list[str]] = {}
    for commit, tag in map(
        str.split,
        context.run(
            r"git for-each-ref --format '%(objectname) %(refname:short)' refs/tags",
            hide=True,
        ).stdout.splitlines(),
    ):
        tags_per_commit.setdefault(commit, []).append(tag)

    current_commit = context.run(
        "git rev-parse HEAD", silent=True, external=True
    ).stdout.strip()
    tags = set(tags_per_commit.get(current_commit, set()))

    if not tags:
        log.error("No tags found for current commit")

    for t in tags:
        if not TAG_PATTERN.match(t):
            msg = f"Invalid tag: {t}"
            raise Exit(msg)

    log.info(f"Found tags: {tags}")

    return tags


def parse_tag(tag: str) -> TagInfo:
    match = TAG_PATTERN.match(tag)
    if not match:
        msg = f"Invalid tag: {tag}"
        raise Exit(msg)

    version = match.group("version")
    if not semver.Version.is_valid(version):
        raise Exit(f"Invalid version: {version} in tag {tag}")

    return TagInfo(tag=tag, name=match.group("name"), version=match.group("version"))


@dataclass
class TagInfo:
    tag: str
    name: str
    version: str


def prepare_js_release(
    context: Context, package: PackageInfo
) -> Callable[[bool], None]:
    node_auth_token = os.getenv("NODE_AUTH_TOKEN")
    if node_auth_token is None:
        msg = "NODE_AUTH_TOKEN environment variable must be set"
        raise Exit(msg)

    with context.cd(JS_DIR):
        context.run("npm ci")
        context.run("npm run build")

    def publish(dry_run: bool) -> None:
        with context.cd(JS_DIR):
            if dry_run:
                context.run(f"npm --workspace {package.name} pack --dry-run")
                return
            context.run(
                f"npm --workspace {package.name} publish --access public",
                env_dict={"NODE_AUTH_TOKEN": node_auth_token},
            )

    return publish


def prepare_py_release(
    context: Context, package: PackageInfo
) -> Callable[[bool], None]:
    twine_username = os.getenv("PYPI_USERNAME")
    twine_password = os.getenv("PYPI_PASSWORD")

    if not (twine_password and twine_username):
        msg = "PYPI_USERNAME and PYPI_PASSWORD environment variables must be set"
        raise Exit(msg)

    for build_dir_name in ["build", "dist"]:
        build_dir_path = Path.cwd() / build_dir_name
        if build_dir_path.exists():
            rmtree(str(build_dir_path))

    with context.cd(package.path):
        context.run("hatch build")

    def publish(dry_run: bool):
        with context.cd(package.path):
            if dry_run:
                context.run("twine check dist/*")
                return

            context.run(
                "twine upload dist/*",
                env_dict={
                    "TWINE_USERNAME": twine_username,
                    "TWINE_PASSWORD": twine_password,
                },
            )

    return publish
