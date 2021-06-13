import pytest

from idom.web.utils import resolve_module_exports_from_source
from tests.general_utils import assert_same_items


@pytest.mark.parametrize(
    "module_source, expected_names, expected_references",
    [
        (
            "asdfasdfasdf;export{one as One, two as Two};asdfasdf;",
            ["One", "Two"],
            [],
        ),
        (
            "asd;export{one as One};asdfasdf;export{two as Two};",
            ["One", "Two"],
            [],
        ),
        ("asdasd;export default something;", ["default"], []),
        (
            "asdasd;export One something;asdfa;export Two somethingElse;",
            ["One", "Two"],
            [],
        ),
        (
            "asdasd;export One something;asdfa;export{two as Two};asdfasdf;",
            ["One", "Two"],
            [],
        ),
    ],
)
def test_resolve_module_exports_from_source(
    module_source, expected_names, expected_references
):
    names, references = resolve_module_exports_from_source(module_source)
    assert_same_items(names, expected_names)
    assert_same_items(references, expected_references)
