import asyncio
import threading
import time
from contextlib import ExitStack
from pathlib import Path

import pytest
from playwright.async_api import Page

from idom.sample import SampleApp as SampleApp
from idom.server import flask as flask_implementation
from idom.server.utils import find_available_port
from idom.server.utils import run as sync_run
from idom.server.utils import traversal_safe_path
from tests.tooling.loop import open_event_loop


@pytest.fixture
def exit_stack():
    with ExitStack() as es:
        yield es


def test_find_available_port():
    assert find_available_port("localhost", port_min=5000, port_max=6000)
    with pytest.raises(RuntimeError, match="no available port"):
        # check that if port range is exhausted we raise
        find_available_port("localhost", port_min=0, port_max=0)


async def test_run(page: Page, exit_stack: ExitStack):
    loop = exit_stack.enter_context(open_event_loop(as_current=False))

    host = "127.0.0.1"
    port = find_available_port(host)
    url = f"http://{host}:{port}"

    def run_in_thread():
        asyncio.set_event_loop(loop)
        sync_run(
            SampleApp,
            host,
            port,
            implementation=flask_implementation,
        )

    threading.Thread(target=run_in_thread, daemon=True).start()

    # give the server a moment to start
    time.sleep(0.5)

    await page.goto(url)
    await page.wait_for_selector("#sample")


@pytest.mark.parametrize(
    "bad_path",
    [
        "../escaped",
        "ok/../../escaped",
        "ok/ok-again/../../ok-yet-again/../../../escaped",
    ],
)
def test_catch_unsafe_relative_path_traversal(tmp_path, bad_path):
    with pytest.raises(ValueError, match="Unsafe path"):
        traversal_safe_path(tmp_path, *bad_path.split("/"))


def test_catch_unsafe_symlink_path_traversal(tmp_path):
    symlink: Path = tmp_path / "file.txt"
    symlink.symlink_to(tmp_path.parent / "escaped-file.txt")
    with pytest.raises(ValueError, match="Unsafe path"):
        traversal_safe_path(tmp_path, "file.txt")
