import asyncio

import pytest

import idom


def test_serve_has_loop_attribute(server):
    assert isinstance(server.loop, asyncio.AbstractEventLoop)


def test_no_application_until_running():
    @idom.element
    async def AnElement(self):
        pass

    server = idom.server.sanic.PerClientStateServer(AnElement)

    with pytest.raises(RuntimeError, match="No application"):
        server.application
