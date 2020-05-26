from subprocess import CalledProcessError
from unittest import mock

import pytest

from idom import client

from .utils import assert_file_is_touched


@pytest.mark.slow
def test_install():
    client.delete_web_modules(["jquery"], skip_missing=True)
    client.install("jquery")
    assert client.web_module_exists("jquery")
    with assert_file_is_touched(client.web_module_path("jquery")):
        client.install("jquery", force=True)
    client.delete_web_modules("jquery")


@pytest.mark.slow
def test_install_namespace_package():
    client.install("@material-ui/core")
    assert client.web_module_exists("@material-ui/core")
    expected = "../web_modules/@material-ui/core.js"
    assert client.web_module("@material-ui/core") == expected


def test_raise_on_missing_import_path():
    with pytest.raises(ValueError, match="does not exist"):
        client.web_module("module/that/does/not/exist")


called_process_error = CalledProcessError(1, "failing-cmd")
called_process_error.stderr = b"an error occured"


@mock.patch("subprocess.run", side_effect=called_process_error)
def test_bad_subprocess_call(subprocess_run, caplog):
    with pytest.raises(CalledProcessError):
        client.install(["victory"])
    assert "an error occured" in caplog.text
