from pathlib import Path
from subprocess import CalledProcessError
from unittest import mock

import pytest

from idom import client


@pytest.mark.slow
def test_install():
    client.delete_web_modules(["jquery"], skip_missing=True)
    client.install("jquery")

    assert client.web_module_exists("jquery")
    assert client.web_module_exists("/jquery")  # works with a leading slash too
    assert "jquery" in client.installed()

    with pytest.raises(ValueError, match="already exists"):
        # can't register a module with the same name
        client.register_web_module("jquery", Path() / "some-module.js")

    client.delete_web_modules("jquery")
    assert not client.web_module_exists("jquery")
    assert "jquery" not in client.installed()


@pytest.mark.slow
def test_install_namespace_package():
    client.install("@material-ui/core")
    assert client.web_module_exists("@material-ui/core")
    expected = "../web_modules/@material-ui/core.js"
    assert client.web_module_url("@material-ui/core") == expected


def test_raise_on_missing_import_path():
    with pytest.raises(ValueError, match="does not exist"):
        client.web_module_url("module/that/does/not/exist")


called_process_error = CalledProcessError(1, "failing-cmd")
called_process_error.stderr = b"an error occured"


@mock.patch("subprocess.run", side_effect=called_process_error)
def test_bad_subprocess_call(subprocess_run, caplog):
    with pytest.raises(CalledProcessError):
        client.install(["victory"])
    assert "an error occured" in caplog.text


def test_cannot_register_module_from_non_existant_source():
    with pytest.raises(ValueError, match="does not exist"):
        client.register_web_module("my-module", Path() / "a-non-existant-file.js")

    with pytest.raises(ValueError, match="is not a file"):
        client.register_web_module("my-module", Path("/"))
