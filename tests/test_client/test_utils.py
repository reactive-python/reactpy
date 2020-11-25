from idom.client.utils import open_modifiable_json


def test_open_modifiable_json(tmp_path):
    temp_json = tmp_path / "data.json"

    temp_json.touch()

    with open_modifiable_json(temp_json) as data:
        assert data == {}
        data["x"] = 1

    with open_modifiable_json(temp_json) as updated_data:
        assert updated_data == {"x": 1}
