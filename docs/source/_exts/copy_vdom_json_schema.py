import json
from pathlib import Path

from sphinx.application import Sphinx

from idom.core.vdom import SERIALIZED_VDOM_JSON_SCHEMA


def setup(app: Sphinx) -> None:
    schema_file = Path(__file__).parent.parent / "vdom-json-schema.json"
    current_schema = json.dumps(SERIALIZED_VDOM_JSON_SCHEMA, indent=2, sort_keys=True)

    # We need to make this check because the autoreload system for the docs checks
    # to see if the file has changed to determine whether to re-build. Thus we should
    # only write to the file if its contents will be different.
    if not schema_file.exists() or schema_file.read_text() != current_schema:
        schema_file.write_text(current_schema)
