from __future__ import annotations

import contextlib
import os
import subprocess

import pytest
from _pytest.config.argparsing import Parser
from filelock import FileLock

from reactpy.config import (
    REACTPY_ASYNC_RENDERING,
    REACTPY_DEBUG,
)
from reactpy.testing import (
    BackendFixture,
    DisplayFixture,
    capture_reactpy_logs,
    clear_reactpy_web_modules_dir,
)
from reactpy.testing.common import GITHUB_ACTIONS

REACTPY_ASYNC_RENDERING.set_current(True)
REACTPY_DEBUG.set_current(True)


def pytest_addoption(parser: Parser) -> None:
    parser.addoption(
        "--headless",
        dest="headless",
        action="store_true",
        help="Don't open a browser window when running web-based tests",
    )


def headless_environ(pytestconfig: pytest.Config):
    if (
        pytestconfig.getoption("headless")
        or os.environ.get("PLAYWRIGHT_HEADLESS") == "1"
        or GITHUB_ACTIONS
    ):
        os.environ["PLAYWRIGHT_HEADLESS"] = "1"
        return True
    return False


def get_lock_dir(tmp_path_factory, worker_id):
    if worker_id == "master":
        return tmp_path_factory.getbasetemp()
    return tmp_path_factory.getbasetemp().parent


@pytest.fixture(autouse=True, scope="session")
def install_playwright(tmp_path_factory, worker_id):
    root_tmp_dir = get_lock_dir(tmp_path_factory, worker_id)
    fn = root_tmp_dir / "playwright_install.lock"
    flag = root_tmp_dir / "playwright_install.done"

    with FileLock(str(fn)):
        if not flag.exists():
            subprocess.run(["playwright", "install", "chromium"], check=True)  # noqa: S607
            # Try to install system deps, but don't fail if already installed or no root access
            with contextlib.suppress(subprocess.CalledProcessError):
                subprocess.run(["playwright", "install-deps"], check=True)  # noqa: S607
            flag.touch()


@pytest.fixture(autouse=True, scope="session")
def rebuild(tmp_path_factory, worker_id):
    # When running inside `hatch test`, the `HATCH_ENV_ACTIVE` environment variable
    # is set. If we try to run `hatch build` with this variable set, Hatch will
    # complain that the current environment is not a builder environment.
    # To fix this, we remove `HATCH_ENV_ACTIVE` from the environment variables
    # passed to the subprocess.
    env = os.environ.copy()
    env.pop("HATCH_ENV_ACTIVE", None)

    root_tmp_dir = get_lock_dir(tmp_path_factory, worker_id)
    fn = root_tmp_dir / "build.lock"
    flag = root_tmp_dir / "build.done"

    # Whoever gets the lock first performs the build.
    with FileLock(str(fn)):
        if not flag.exists():
            subprocess.run(["hatch", "build", "-t", "wheel"], check=True, env=env)  # noqa: S607
            flag.touch()


@pytest.fixture(scope="session")
async def display(server, browser):
    async with DisplayFixture(backend=server, browser=browser) as display:
        yield display


@pytest.fixture(scope="session")
async def server():
    async with BackendFixture() as server:
        yield server


@pytest.fixture(scope="session")
async def browser(pytestconfig: pytest.Config):
    from playwright.async_api import async_playwright

    async with async_playwright() as pw:
        yield await pw.chromium.launch(headless=headless_environ(pytestconfig))


@pytest.fixture(autouse=True)
def clear_web_modules_dir_after_test():
    clear_reactpy_web_modules_dir()


@pytest.fixture(autouse=True)
def assert_no_logged_exceptions():
    with capture_reactpy_logs() as records:
        yield
        try:
            for r in records:
                if r.exc_info is not None:
                    raise r.exc_info[1]
        finally:
            records.clear()
