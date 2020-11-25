import json
from pathlib import Path
from contextlib import contextmanager
from typing import Iterator, Any


@contextmanager
def open_modifiable_json(path: Path) -> Iterator[Any]:
    with path.open() as f:
        data = json.loads(f.read().strip() or "{}")

    yield data

    with path.open("w") as f:
        json.dump(data, f)
