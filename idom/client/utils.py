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


_JS_MODULE_EXPORT_PATTERN = re.compile(r";export{(.*?)};")
_JS_MODULE_EXPORT_NAME_PATTERN = re.compile(r";export (.*?) .*?;")


def find_js_module_exports(path: Path) -> List[str]:
    names: List[str] = []
    if path.suffix != ".js":
        # we only know how to do this for javascript modules
        return []
    with path.open() as f:
        content = f.read()
        for match in _JS_MODULE_EXPORT_PATTERN.findall(content):
            for export in match.split(","):
                names.append(export.split(" as ", 1)[1].strip())
        names.extend(_JS_MODULE_EXPORT_NAME_PATTERN.findall(content))
    return names
