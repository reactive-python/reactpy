# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

import logging
from glob import glob
from pathlib import Path

# Delete old `.coverage*` files in the project root
print("Deleting old coverage files...")  # noqa: T201
root_dir = Path(__file__).parent.parent.parent
coverage_files = glob(str(root_dir / ".coverage*"))

for path in coverage_files:
    coverage_file = Path(path)
    if coverage_file.exists():
        try:
            coverage_file.unlink()
        except Exception as e:
            logging.error(f"Failed to delete {coverage_file}: {e}")
