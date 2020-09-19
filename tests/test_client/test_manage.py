from pathlib import Path
from subprocess import CalledProcessError
from unittest import mock

import pytest

from idom.client.manage import (
    install,
    installed,
    delete_web_modules,
    register_web_module,
    web_module_exists,
    web_module_url,
)


@pytest.mark.slow
def test_install():
    delete_web_modules(["jquery"], skip_missing=True)
    install("jquery")

    assert web_module_exists("jquery")
    assert web_module_exists("/jquery")  # works with a leading slash too
    assert "jquery" in installed()

    with pytest.raises(ValueError, match="already exists"):
        # can't register a module with the same name
        register_web_module("jquery", Path() / "some-module.js")

    delete_web_modules("jquery")
    assert not web_module_exists("jquery")
    assert "jquery" not in installed()


@pytest.mark.slow
def test_install_namespace_package():
    install("@material-ui/core")
    assert web_module_exists("@material-ui/core")
    expected = "../web_modules/@material-ui/core.js"
    assert web_module_url("@material-ui/core") == expected


def test_error_on_delete_not_exists():
    with pytest.raises(ValueError, match=r"Module .*? does not exist"):
        delete_web_modules("module/that/does/not/exist")


def test_raise_on_missing_import_path():
    with pytest.raises(ValueError, match="does not exist"):
        web_module_url("module/that/does/not/exist")


called_process_error = CalledProcessError(1, "failing-cmd")
called_process_error.stderr = b"an error occured"


@mock.patch("subprocess.run", side_effect=called_process_error)
def test_bad_subprocess_call(subprocess_run, caplog):
    with pytest.raises(CalledProcessError):
        install(["victory"])
    assert "an error occured" in caplog.text


def test_cannot_register_module_from_non_existant_source():
    with pytest.raises(ValueError, match="does not exist"):
        register_web_module("my-module", Path() / "a-non-existant-file.js")

    with pytest.raises(ValueError, match="is not a file"):
        register_web_module("my-module", Path("/"))
