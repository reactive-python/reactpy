import pytest

from idom.client.utils import open_modifiable_json, find_js_module_exports_in_source

from tests.general_utils import assert_same_items


def test_open_modifiable_json(tmp_path):
    temp_json = tmp_path / "data.json"

    temp_json.touch()

    with open_modifiable_json(temp_json) as data:
        assert data == {}
        data["x"] = 1

    with open_modifiable_json(temp_json) as updated_data:
        assert updated_data == {"x": 1}


@pytest.mark.parametrize(
    "module_source, expected_names",
    [
        ("asdfasdfasdf;export{one as One, two as Two};asdfasdf;", ["One", "Two"]),
        ("asd;export{one as One};asdfasdf;export{two as Two};", ["One", "Two"]),
        ("asdasd;export default something;", ["default"]),
        ("asdasd;export One something;asdfa;export Two somethingElse;", ["One", "Two"]),
        (
            "asdasd;export One something;asdfa;export{two as Two};asdfasdf;",
            ["One", "Two"],
        ),
    ],
)
def test_find_js_module_exports_in_source(module_source, expected_names):
    assert_same_items(find_js_module_exports_in_source(module_source), expected_names)
