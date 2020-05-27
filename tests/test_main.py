import pytest

from idom.__main__ import main
from idom import client

from tests.test_client.utils import assert_file_is_touched


@pytest.mark.slow
def test_simple_console_install(capsys):
    client.delete_web_modules("jquery", skip_missing=True)

    main("install", "jquery")
    assert client.web_module_exists("jquery")
    main("installed")
    captured = capsys.readouterr()
    assert "- jquery" in captured.out

    with assert_file_is_touched(client.web_module_path("jquery")):
        main("install", "jquery", "--force")
    assert client.web_module_exists("jquery")

    main("uninstall", "jquery")
    assert not client.web_module_exists("jquery")


@pytest.mark.slow
def test_console_install_with_exports(capsys):
    client.delete_web_modules(["preact", "preact/hooks"], skip_missing=True)

    main("install", "preact", "--exports", "preact/hooks")
    assert client.web_module_exists("preact/hooks")
    main("installed")
    captured = capsys.readouterr()
    assert "- preact" in captured.out
    assert "- preact/hooks" in captured.out

    main("uninstall", "preact")
    assert not client.web_module_exists("preact/hooks")
    main("installed")
    captured = capsys.readouterr()
    assert "- preact" not in captured.out
    assert "- preact/hooks" not in captured.out


def test_bad_options_for_uninstall(capsys):
    with pytest.raises(SystemExit):
        main("uninstall", "--exports", "x")
    captured = capsys.readouterr()
    assert captured.out == "ERROR: uninstall does not support the '--exports' option\n"

    with pytest.raises(SystemExit):
        main("uninstall", "--force")
    captured = capsys.readouterr()
    assert captured.out == "ERROR: uninstall does not support the '--force' option\n"
