# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

# ruff: noqa: INP001
import logging
import re
import shutil
import sys
from pathlib import Path


def copy_files(source: Path, destination: Path, pattern: str) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir()

    for file in source.iterdir():
        if file.is_file():
            if not pattern or re.match(pattern, file.name):
                shutil.copy(file, destination / file.name)
        else:
            copy_files(file, destination / file.name, pattern)


if __name__ == "__main__":
    if len(sys.argv) not in {3, 4}:
        logging.error(
            "Script used incorrectly!\nUsage: python copy_dir.py <source_dir> <destination> <optional:match_pattern>"
        )
        sys.exit(1)

    root_dir = Path(__file__).parent.parent.parent
    _source = Path(root_dir / sys.argv[1])
    _destintation = Path(root_dir / sys.argv[2])
    _pattern = sys.argv[3] if len(sys.argv) == 4 else ""  # noqa

    if not _source.exists():
        logging.error("Source directory %s does not exist", _source)
        sys.exit(1)

    copy_files(_source, _destintation, _pattern)
