import threading
import time
from contextlib import ExitStack

import pytest
from playwright.async_api import Page

from reactpy.backend import flask as flask_implementation
from reactpy.backend.utils import find_available_port
from reactpy.backend.utils import run as sync_run
from reactpy.sample import SampleApp


@pytest.fixture
def exit_stack():
    with ExitStack() as es:
        yield es


def test_find_available_port():
    assert find_available_port("localhost", port_min=5000, port_max=6000)
    with pytest.raises(RuntimeError, match="no available port"):
        # check that if port range is exhausted we raise
        find_available_port("localhost", port_min=0, port_max=0)


async def test_run(page: Page):
    host = "127.0.0.1"
    port = find_available_port(host)
    url = f"http://{host}:{port}"

    threading.Thread(
        target=lambda: sync_run(
            SampleApp,
            host,
            port,
            implementation=flask_implementation,
        ),
        daemon=True,
    ).start()

    # give the server a moment to start
    time.sleep(0.5)

    await page.goto(url)
    await page.wait_for_selector("#sample")
