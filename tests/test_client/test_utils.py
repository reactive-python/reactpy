import pytest

from idom.client.utils import split_package_name_and_version, open_modifiable_json


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


def test_open_modifiable_json(tmp_path):
    temp_json = tmp_path / "data.json"

    temp_json.touch()

    with open_modifiable_json(temp_json) as data:
        assert data == {}
        data["x"] = 1

    with open_modifiable_json(temp_json) as updated_data:
        assert updated_data == {"x": 1}
