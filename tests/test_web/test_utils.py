from pathlib import Path

import pytest
import responses

from idom.web.utils import (
    resolve_module_exports_from_file,
    resolve_module_exports_from_source,
    resolve_module_exports_from_url,
)


JS_FIXTURES_DIR = Path(__file__).parent / "js_fixtures"


@responses.activate
def test_resolve_module_exports_from_file(caplog):
    responses.add(
        responses.GET,
        "https://some.external.url",
        body="export {something as ExternalUrl}",
    )
    path = JS_FIXTURES_DIR / "export-resolution" / "index.js"
    assert resolve_module_exports_from_file(path, 4) == {
        "Index",
        "One",
        "Two",
        "ExternalUrl",
    }


def test_resolve_module_exports_from_file_log_on_max_depth(caplog):
    path = JS_FIXTURES_DIR / "export-resolution" / "index.js"
    assert resolve_module_exports_from_file(path, 0) == set()
    assert len(caplog.records) == 1
    assert caplog.records[0].message.endswith("max depth reached")

    caplog.records.clear()

    assert resolve_module_exports_from_file(path, 2) == {"Index", "One"}
    assert len(caplog.records) == 1
    assert caplog.records[0].message.endswith("max depth reached")


def test_resolve_module_exports_from_file_log_on_unknown_file_location(
    caplog, tmp_path
):
    file = tmp_path / "some.js"
    file.write_text("export * from './does-not-exist.js';")
    resolve_module_exports_from_file(file, 2)
    assert len(caplog.records) == 1
    assert caplog.records[0].message.startswith(
        "Did not resolve exports for unknown file"
    )


@responses.activate
def test_resolve_module_exports_from_url():
    responses.add(
        responses.GET,
        "https://first.url",
        body="export const First = 1; export * from 'https://second.url';",
    )
    responses.add(
        responses.GET,
        "https://second.url",
        body="export const Second = 2;",
    )

    assert resolve_module_exports_from_url("https://first.url", 2) == {
        "First",
        "Second",
    }


def test_resolve_module_exports_from_url_log_on_max_depth(caplog):
    assert resolve_module_exports_from_url("https://some.url", 0) == set()
    assert len(caplog.records) == 1
    assert caplog.records[0].message.endswith("max depth reached")


def test_resolve_module_exports_from_url_log_on_bad_response(caplog):
    assert resolve_module_exports_from_url("https://some.url", 1) == set()
    assert len(caplog.records) == 1
    assert caplog.records[0].message.startswith("Did not resolve exports for url")


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
    names, references = resolve_module_exports_from_source(text)
    assert names == {"default"} and not references


def test_resolve_module_exports_from_source():
    fixture_file = JS_FIXTURES_DIR / "exports-syntax.js"
    names, references = resolve_module_exports_from_source(fixture_file.read_text())
    assert (
        names
        == (
            {f"name{i}" for i in range(1, 21)}
            | {
                "functionName",
                "ClassName",
            }
        )
        and references == {"https://source1.com", "https://source2.com"}
    )
