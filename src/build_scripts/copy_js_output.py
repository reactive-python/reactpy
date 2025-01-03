from pathlib import Path
from shutil import copytree, rmtree

output_dir = Path(__file__).parent.parent / "reactpy" / "static"
source_dir = Path(__file__).parent.parent / "js" / "app" / "dist"
rmtree(output_dir, ignore_errors=True)
copytree(source_dir, output_dir)
print("JavaScript output copied to reactpy/static")  # noqa: T201
