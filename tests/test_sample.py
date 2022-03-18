from idom.sample import App, run_sample_app
from idom.server.utils import find_available_port
from tests import Display


async def test_sample_app(display: Display):
    await display.show(App)
