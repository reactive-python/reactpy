from pathlib import Path
from unittest import mock
from urllib.error import URLError
from uuid import uuid4

import orjson
import pytest

from reactpy.executors.pyscript import utils


def test_bad_root_name():
    file_path = str(
        Path(__file__).parent / "pyscript_components" / "custom_root_name.py"
    )

    with pytest.raises(ValueError):
        utils.pyscript_executor_html((file_path,), uuid4().hex, "bad")


def test_extend_pyscript_config():
    extra_py = ["orjson", "tabulate"]
    extra_js = {"/static/foo.js": "bar"}
    config = {"packages_cache": "always"}

    result = utils.extend_pyscript_config(extra_py, extra_js, config)
    result = orjson.loads(result)

    # Check whether `packages` have been combined
    assert "orjson" in result["packages"]
    assert "tabulate" in result["packages"]
    assert any("reactpy" in package for package in result["packages"])

    # Check whether `js_modules` have been combined
    assert "/static/foo.js" in result["js_modules"]["main"]
    assert any("morphdom" in module for module in result["js_modules"]["main"])

    # Check whether `packages_cache` has been overridden
    assert result["packages_cache"] == "always"


def test_extend_pyscript_config_string_values():
    extra_py = []
    extra_js = {"/static/foo.js": "bar"}
    config = {"packages_cache": "always"}

    # Try using string based `extra_js` and `config`
    extra_js_string = orjson.dumps(extra_js).decode()
    config_string = orjson.dumps(config).decode()
    result = utils.extend_pyscript_config(extra_py, extra_js_string, config_string)
    result = orjson.loads(result)

    # Make sure `packages` is unmangled
    assert any("reactpy" in package for package in result["packages"])

    # Check whether `js_modules` have been combined
    assert "/static/foo.js" in result["js_modules"]["main"]
    assert any("morphdom" in module for module in result["js_modules"]["main"])

    # Check whether `packages_cache` has been overridden
    assert result["packages_cache"] == "always"


def test_get_reactpy_versions_https_fail_http_success():
    utils.get_reactpy_versions.cache_clear()

    mock_response = mock.Mock()
    mock_response.status = 200

    # Mock json.load to return data when called with mock_response
    with (
        mock.patch("reactpy.executors.pyscript.utils.request.urlopen") as mock_urlopen,
        mock.patch("reactpy.executors.pyscript.utils.json.load") as mock_json_load,
    ):

        def side_effect(url, timeout):
            if url.startswith("https"):
                raise URLError("Fail")
            return mock_response

        mock_urlopen.side_effect = side_effect
        mock_json_load.return_value = {
            "releases": {"1.0.0": []},
            "info": {"version": "1.0.0"},
        }

        versions = utils.get_reactpy_versions()
        assert versions == {"versions": ["1.0.0"], "latest": "1.0.0"}

        # Verify both calls were made
        assert mock_urlopen.call_count == 2
        assert mock_urlopen.call_args_list[0][0][0].startswith("https")
        assert mock_urlopen.call_args_list[1][0][0].startswith("http")


def test_get_reactpy_versions_all_fail():
    utils.get_reactpy_versions.cache_clear()

    with (
        mock.patch("reactpy.executors.pyscript.utils.request.urlopen") as mock_urlopen,
        mock.patch("reactpy.executors.pyscript.utils._logger") as mock_logger,
    ):
        mock_urlopen.side_effect = URLError("Fail")

        versions = utils.get_reactpy_versions()
        assert versions == {}

        # Verify exception was logged
        assert mock_logger.exception.called
