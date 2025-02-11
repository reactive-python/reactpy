from pathlib import Path
from uuid import uuid4

import orjson
import pytest

from reactpy.pyscript import utils


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
