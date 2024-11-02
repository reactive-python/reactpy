from pathlib import Path
from shutil import copytree, rmtree

output_dir = Path(__file__).parent.parent / "reactpy" / "_static"
source_dir = Path(__file__).parent.parent.parent.parent / "js" / "app" / "dist"

# Remove the output directory if it exists
rmtree(output_dir, ignore_errors=True)

# Copy the source directory to the output directory
copytree(source_dir, output_dir)

print("JavaScript output copied to reactpy/_static")
