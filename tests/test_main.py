import pytest

from idom.__main__ import main
from idom import client

from tests.general_utils import assert_same_items


@pytest.mark.slow
def test_simple_install(capsys):
    client.delete_web_modules("jquery", skip_missing=True)

    main("install", "jquery")
    assert client.web_module_exists("jquery")
    main("installed")
    captured = capsys.readouterr()
    assert "- jquery" in captured.out

    main("uninstall", "jquery")
    assert not client.web_module_exists("jquery")


@pytest.mark.slow
def test_install_with_exports(capsys):
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


@pytest.mark.slow
def test_restore(capsys):
    main("restore")
    assert_same_items(client.installed(), ["fast-json-patch", "htm", "preact/compat"])


@pytest.mark.parametrize(
    "args, error",
    [
        (("uninstall", "x", "--exports"), ValueError("does not support exports")),
        (("installed", "--exports"), ValueError("does not support exports")),
        (("restore", "--exports"), ValueError("does not support exports")),
    ],
)
def test_bad_options(capsys, args, error):
    with pytest.raises(type(error), match=str(error)):
        main("--debug", *args)
    with pytest.raises(SystemExit):
        main(*args)
