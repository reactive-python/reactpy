import re
import json
from pathlib import Path
from contextlib import contextmanager
from typing import Iterator, Any, List


@contextmanager
def open_modifiable_json(path: Path) -> Iterator[Any]:
    with path.open() as f:
        data = json.loads(f.read().strip() or "{}")

    yield data

    with path.open("w") as f:
        json.dump(data, f)


_JS_VARIABLE_NAME = r"[a-zA-Z_$][0-9a-zA-Z_$]*"
_JS_MODULE_EXPORT_PATTERN = re.compile(f";export{({_JS_VARIABLE_NAME})};")
_JS_MODULE_EXPORT_NAME_PATTERN = re.compile(
    f";export ({_JS_VARIABLE_NAME}) {_JS_VARIABLE_NAME};"
)


def find_js_module_exports_in_source(content: str) -> List[str]:
    names: List[str] = []
    for match in _JS_MODULE_EXPORT_PATTERN.findall(content):
        for export in match.split(","):
            export_parts = export.split(" as ", 1)
            print(export_parts)
            names.append(export_parts[1].strip())
    names.extend(_JS_MODULE_EXPORT_NAME_PATTERN.findall(content))
    return names
