from pathlib import Path
from unittest.mock import patch

import pytest
import responses

from reactpy.reactjs.module import module_name_suffix
from reactpy.reactjs.utils import (
    copy_file,
    file_lock,
    normalize_url_path,
    resolve_names_from_file,
    resolve_names_from_source,
    resolve_names_from_url,
)
from reactpy.testing import assert_reactpy_did_log

JS_FIXTURES_DIR = Path(__file__).parent / "js_fixtures"


@pytest.mark.parametrize(
    "name, suffix",
    [
        ("module", ".js"),
        ("module.ext", ".ext"),
        ("module@x.y.z", ".js"),
        ("module.ext@x.y.z", ".ext"),
        ("@namespace/module", ".js"),
        ("@namespace/module.ext", ".ext"),
        ("@namespace/module@x.y.z", ".js"),
        ("@namespace/module.ext@x.y.z", ".ext"),
    ],
)
def test_module_name_suffix(name, suffix):
    assert module_name_suffix(name) == suffix


@responses.activate
def test_resolve_module_exports_from_file():
    responses.add(
        responses.GET,
        "https://some.external.url",
        body="export {something as ExternalUrl}",
    )
    path = JS_FIXTURES_DIR / "export-resolution" / "index.js"
    assert resolve_names_from_file(path, 4) == {
        "Index",
        "One",
        "Two",
        "ExternalUrl",
    }


def test_resolve_module_exports_from_file_log_on_max_depth(caplog):
    path = JS_FIXTURES_DIR / "export-resolution" / "index.js"
    assert resolve_names_from_file(path, 0) == set()
    assert len(caplog.records) == 1
    assert caplog.records[0].message.endswith("max depth reached")

    caplog.records.clear()

    assert resolve_names_from_file(path, 2) == {"Index", "One"}
    assert len(caplog.records) == 1
    assert caplog.records[0].message.endswith("max depth reached")


def test_resolve_module_exports_from_file_log_on_unknown_file_location(
    caplog, tmp_path
):
    file = tmp_path / "some.js"
    file.write_text("export * from './does-not-exist.js';")
    resolve_names_from_file(file, 2)
    assert len(caplog.records) == 1
    assert caplog.records[0].message.startswith(
        "Did not resolve imports for unknown file"
    )


@responses.activate
def test_resolve_module_exports_from_url():
    responses.add(
        responses.GET,
        "https://some.url/first.js",
        body="export const First = 1; export * from 'https://another.url/path/second.js';",
    )
    responses.add(
        responses.GET,
        "https://another.url/path/second.js",
        body="export const Second = 2; export * from '../third.js';",
    )
    responses.add(
        responses.GET,
        "https://another.url/third.js",
        body="export const Third = 3; export * from './fourth.js';",
    )
    responses.add(
        responses.GET,
        "https://another.url/fourth.js",
        body="export const Fourth = 4;",
    )

    assert resolve_names_from_url("https://some.url/first.js", 4) == {
        "First",
        "Second",
        "Third",
        "Fourth",
    }


def test_resolve_module_exports_from_url_log_on_max_depth(caplog):
    assert resolve_names_from_url("https://some.url", 0) == set()
    assert len(caplog.records) == 1
    assert caplog.records[0].message.endswith("max depth reached")


def test_resolve_module_exports_from_url_log_on_bad_response(caplog):
    assert resolve_names_from_url("https://some.url", 1) == set()
    assert len(caplog.records) == 1
    assert caplog.records[0].message.startswith("Did not resolve imports for url")


@pytest.mark.parametrize(
    "text",
    [
        "export default expression;",
        "export default function (…) { … } // also class, function*",
        "export default function name1(…) { … } // also class, function*",
        "export { something as default };",
        "export { default } from 'some-source';",
        "export { something as default } from 'some-source';",
    ],
)
def test_resolve_module_default_exports_from_source(text):
    names, references = resolve_names_from_source(text, exclude_default=False)
    assert names == {"default"} and not references


def test_resolve_module_exports_from_source():
    fixture_file = JS_FIXTURES_DIR / "exports-syntax.js"
    names, references = resolve_names_from_source(
        fixture_file.read_text(), exclude_default=False
    )
    assert names == (
        {f"name{i}" for i in range(1, 21)}
        | {
            "functionName",
            "ClassName",
        }
    ) and references == {"https://source1.com", "https://source2.com"}


def test_log_on_unknown_export_type():
    with assert_reactpy_did_log(match_message="Found unknown export "):
        assert resolve_names_from_source(
            "export something unknown;", exclude_default=False
        ) == (set(), set())


def test_resolve_relative_url():
    assert (
        normalize_url_path("https://some.url", "path/to/another.js")
        == "path/to/another.js"
    )
    assert (
        normalize_url_path("https://some.url", "/path/to/another.js")
        == "https://some.url/path/to/another.js"
    )
    assert normalize_url_path("/some/path", "to/another.js") == "to/another.js"


def test_copy_file_fallback(tmp_path):
    source = tmp_path / "source.txt"
    source.write_text("content")
    target = tmp_path / "target.txt"

    path_cls = type(target)

    with patch("shutil.copy"):
        with patch.object(
            path_cls, "replace", side_effect=[OSError, OSError]
        ) as mock_replace:
            with patch.object(path_cls, "rename") as mock_rename:
                with patch.object(path_cls, "exists", return_value=True):
                    with patch.object(path_cls, "unlink") as mock_unlink:
                        with patch("time.sleep"):  # Speed up test
                            copy_file(target, source, symlink=False)

                        assert mock_replace.call_count == 2
                        mock_unlink.assert_called_once()
                        mock_rename.assert_called_once()


def test_simple_file_lock_timeout(tmp_path):
    lock_file = tmp_path / "lock"

    with patch("os.open", side_effect=OSError):
        with patch("time.sleep"):  # Speed up test
            with pytest.raises(TimeoutError, match="Could not acquire lock"):
                with file_lock(lock_file, timeout=0.1):
                    pass
