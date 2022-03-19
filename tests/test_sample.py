from idom.sample import App, run_sample_app
from idom.server.utils import find_available_port
from idom.testing import DisplayFixture


async def test_sample_app(display: DisplayFixture):
    await display.show(App)
