from pathlib import Path

import pytest

from idom.web.utils import resolve_module_exports_from_source


JS_FIXTURES_DIR = Path(__file__).parent / "js_fixtures"


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
        and references == {"source1", "source2"}
    )
