import asyncio

import pytest

import idom


@pytest.fixture(scope="module")
def mount_and_server(fixturized_server_type, host, port, last_server_error):
    return idom.server.multiview_server(
        fixturized_server_type,
        host,
        port,
        server_options={"last_server_error": last_server_error},
        run_options={"debug": True},
        # use the default app for the server just to get test coverage there
        app=None,
    )


def test_serve_has_loop_attribute(server):
    assert isinstance(server.loop, asyncio.AbstractEventLoop)


def test_no_application_until_running():
    @idom.element
    async def AnElement(self):
        pass

    server = idom.server.sanic.PerClientStateServer(AnElement)

    with pytest.raises(RuntimeError, match="No application"):
        server.application
