import pytest

from idom.console import main
from idom import client

from tests.test_client.utils import assert_file_is_touched


@pytest.mark.slow
def test_simple_console_install():
    client.delete_web_modules("jquery", skip_missing=True)
    main("install", "jquery")
    assert client.web_module_exists("jquery")
    with assert_file_is_touched(client.web_module_path("jquery")):
        main("install", "jquery", "--force")
    assert client.web_module_exists("jquery")
    main("uninstall", "jquery")
    assert not client.web_module_exists("jquery")


@pytest.mark.slow
def test_console_install_with_exports():
    client.delete_web_modules(["preact", "preact/hooks"], skip_missing=True)
    main("install", "preact", "--exports", "preact/hooks")
    assert client.web_module_exists("preact/hooks")


def test_bad_options_for_uninstall():
    printed = []
    with pytest.raises(SystemExit):
        main("uninstall", "--exports", "x", print=printed.append)
    assert printed[-1] == "ERROR: uninstall does not support the '--exports' option"

    printed = []
    with pytest.raises(SystemExit):
        main("uninstall", "--force", print=printed.append)
    assert printed[-1] == "ERROR: uninstall does not support the '--force' option"
