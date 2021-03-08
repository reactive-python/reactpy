import pytest

from idom.client._private import (
    find_js_module_exports_in_source,
    split_package_name_and_version,
)
from tests.general_utils import assert_same_items


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


@pytest.mark.parametrize(
    "package_specifier,expected_name_and_version",
    [
        ("package", ("package", "")),
        ("package@1.2.3", ("package", "1.2.3")),
        ("@scope/pkg", ("@scope/pkg", "")),
        ("@scope/pkg@1.2.3", ("@scope/pkg", "1.2.3")),
        ("alias@npm:package", ("alias", "npm:package")),
        ("alias@npm:package@1.2.3", ("alias", "npm:package@1.2.3")),
        ("alias@npm:@scope/pkg@1.2.3", ("alias", "npm:@scope/pkg@1.2.3")),
        ("@alias/pkg@npm:@scope/pkg@1.2.3", ("@alias/pkg", "npm:@scope/pkg@1.2.3")),
    ],
)
def test_split_package_name_and_version(package_specifier, expected_name_and_version):
    assert (
        split_package_name_and_version(package_specifier) == expected_name_and_version
    )
