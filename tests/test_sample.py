from reactpy.testing import DisplayFixture
from tests.sample import SampleApp

from . import pytestmark  # noqa: F401


async def test_sample_app(display: DisplayFixture):
    await display.show(SampleApp)
    h1 = await display.page.wait_for_selector("h1")
    assert (await h1.text_content()) == "Sample Application"
