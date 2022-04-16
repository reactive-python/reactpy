from idom.sample import SampleApp
from idom.testing import DisplayFixture


async def test_sample_app(display: DisplayFixture):
    await display.show(SampleApp)

    h1 = await display.page.wait_for_selector("h1")
    assert (await h1.text_content()) == "Sample Application"
