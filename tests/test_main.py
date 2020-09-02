import pytest

from idom.__main__ import main
from idom import client

from tests.test_client.utils import assert_file_is_touched


@pytest.mark.slow
def test_simple_install(capsys):
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
    assert client.installed() == ["fast-json-patch", "htm", "react", "react-dom"]


@pytest.mark.parametrize(
    "args, error",
    [
        (("uninstall", "x", "--exports"), ValueError("does not support exports")),
        (("uninstall", "x", "--force"), ValueError("does not support force")),
        (("installed", "--exports"), ValueError("does not support exports")),
        (("installed", "--force"), ValueError("does not support force")),
        (("restore", "--exports"), ValueError("does not support exports")),
        (("restore", "--force"), ValueError("does not support force")),
    ],
)
def test_bad_options(capsys, args, error):
    with pytest.raises(type(error), match=str(error)):
        main("--debug", *args)
    with pytest.raises(SystemExit):
        main(*args)
