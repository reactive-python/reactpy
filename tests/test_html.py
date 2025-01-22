import pytest

from reactpy import component, config, html
from reactpy.testing import DisplayFixture, poll
from reactpy.utils import Ref
from tests.tooling.hooks import use_counter


async def test_script_re_run_on_content_change(display: DisplayFixture):
    incr_count = Ref()

    @component
    def HasScript():
        count, incr_count.current = use_counter(1)
        return html.div(
            html.div({"id": "mount-count", "data_value": 0}),
            html.script(
                f'document.getElementById("mount-count").setAttribute("data-value", {count});'
            ),
        )

    await display.show(HasScript)

    mount_count = await display.page.wait_for_selector("#mount-count", state="attached")
    poll_mount_count = poll(mount_count.get_attribute, "data-value")

    await poll_mount_count.until_equals("1")
    incr_count.current()
    await poll_mount_count.until_equals("2")
    incr_count.current()
    await poll_mount_count.until_equals("3")


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
                html.div({"id": "run-count", "data_value": 0}),
                html.script(
                    {
                        "src": f"/_reactpy/modules/{file_name_template.format(src_id=src_id)}"
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
        html.script({"on_event": lambda: None})


def test_simple_fragment():
    assert html._() == {"tagName": ""}
    assert html._(1, 2, 3) == {"tagName": "", "children": [1, 2, 3]}
    assert html._({"key": "something"}) == {"tagName": "", "key": "something"}
    assert html._({"key": "something"}, 1, 2, 3) == {
        "tagName": "",
        "key": "something",
        "children": [1, 2, 3],
    }


def test_fragment_can_have_no_attributes():
    with pytest.raises(TypeError, match="Fragments cannot have attributes"):
        html._({"some_attribute": 1})
