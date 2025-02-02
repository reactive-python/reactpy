import pytest
from playwright.async_api import expect

from reactpy import component, config, hooks, html
from reactpy.testing import DisplayFixture, poll
from reactpy.utils import Ref
from tests.tooling.common import DEFAULT_TYPE_DELAY
from tests.tooling.hooks import use_counter


async def test_script_re_run_on_content_change(display: DisplayFixture):
    @component
    def HasScript():
        count, set_count = hooks.use_state(0)

        def on_click(event):
            set_count(count + 1)

        return html.div(
            html.div({"id": "mount-count", "dataValue": 0}),
            html.script(
                f'document.getElementById("mount-count").setAttribute("data-value", {count});'
            ),
            html.button({"onClick": on_click, "id": "incr"}, "Increment"),
        )

    await display.show(HasScript)

    await display.page.wait_for_selector("#mount-count", state="attached")
    button = await display.page.wait_for_selector("#incr", state="attached")

    await button.click(delay=DEFAULT_TYPE_DELAY)
    await expect(display.page.locator("#mount-count")).to_have_attribute(
        "data-value", "1"
    )

    await button.click(delay=DEFAULT_TYPE_DELAY)
    await expect(display.page.locator("#mount-count")).to_have_attribute(
        "data-value", "2"
    )

    await button.click(delay=DEFAULT_TYPE_DELAY)
    await expect(display.page.locator("#mount-count")).to_have_attribute(
        "data-value", "3", timeout=100000
    )


async def test_script_from_src(display: DisplayFixture):
    incr_src_id = Ref()
    file_name_template = "__some_js_script_{src_id}__.js"

    @component
    def HasScript():
        src_id, incr_src_id.current = use_counter(0)
        if src_id == 0:
            # on initial display we haven't added the file yet.
            return html.div()
        else:
            return html.div(
                html.div({"id": "run-count", "dataValue": 0}),
                html.script(
                    {
                        "src": f"/reactpy/modules/{file_name_template.format(src_id=src_id)}"
                    }
                ),
            )

    await display.show(HasScript)

    for i in range(1, 4):
        script_file = (
            config.REACTPY_WEB_MODULES_DIR.current / file_name_template.format(src_id=i)
        )
        script_file.write_text(
            f"""
            let runCountEl = document.getElementById("run-count");
            runCountEl.setAttribute("data-value", {i});
            """
        )

        await poll(lambda: hasattr(incr_src_id, "current")).until_is(True)
        incr_src_id.current()

        run_count = await display.page.wait_for_selector("#run-count", state="attached")
        poll_run_count = poll(run_count.get_attribute, "data-value")
        await poll_run_count.until_equals("1")


def test_script_may_only_have_one_child():
    with pytest.raises(ValueError, match="'script' nodes may have, at most, one child"):
        html.script("one child", "two child")


def test_child_of_script_must_be_string():
    with pytest.raises(ValueError, match="The child of a 'script' must be a string"):
        html.script(1)


def test_script_has_no_event_handlers():
    with pytest.raises(ValueError, match="do not support event handlers"):
        html.script({"onEvent": lambda: None})


def test_simple_fragment():
    assert html.fragment() == {"tagName": ""}
    assert html.fragment(1, 2, 3) == {"tagName": "", "children": [1, 2, 3]}
    assert html.fragment({"key": "something"}) == {"tagName": "", "key": "something"}
    assert html.fragment({"key": "something"}, 1, 2, 3) == {
        "tagName": "",
        "key": "something",
        "children": [1, 2, 3],
    }


def test_fragment_can_have_no_attributes():
    with pytest.raises(TypeError, match="Fragments cannot have attributes"):
        html.fragment({"someAttribute": 1})


async def test_svg(display: DisplayFixture):
    @component
    def SvgComponent():
        return html.svg(
            {"width": 100, "height": 100},
            html.svg.circle(
                {"cx": 50, "cy": 50, "r": 40, "fill": "red"},
            ),
            html.svg.circle(
                {"cx": 50, "cy": 50, "r": 40, "fill": "red"},
            ),
        )

    await display.show(SvgComponent)
    svg = await display.page.wait_for_selector("svg", state="attached")
    assert await svg.get_attribute("width") == "100"
    assert await svg.get_attribute("height") == "100"
    circle = await display.page.wait_for_selector("circle", state="attached")
    assert await circle.get_attribute("cx") == "50"
    assert await circle.get_attribute("cy") == "50"
    assert await circle.get_attribute("r") == "40"
    assert await circle.get_attribute("fill") == "red"
