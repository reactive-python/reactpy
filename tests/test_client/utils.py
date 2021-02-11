from contextlib import contextmanager
from pathlib import Path


@contextmanager
def assert_file_is_touched(path):
    path = Path(path)
    last_modified = path.stat().st_mtime
    yield
    assert last_modified != path.stat().st_mtime
