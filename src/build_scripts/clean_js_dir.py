# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

# Deletes `dist`, `node_modules`, and `tsconfig.tsbuildinfo` from all JS packages in the JS source directory.

import contextlib
import glob
import os
import pathlib
import shutil

# Get the path to the JS source directory
js_src_dir = pathlib.Path(__file__).parent.parent / "js"

# Get the paths to all `dist` folders in the JS source directory
dist_dirs = glob.glob(str(js_src_dir / "**/dist"), recursive=True)

# Get the paths to all `node_modules` folders in the JS source directory
node_modules_dirs = glob.glob(str(js_src_dir / "**/node_modules"), recursive=True)

# Get the paths to all `tsconfig.tsbuildinfo` files in the JS source directory
tsconfig_tsbuildinfo_files = glob.glob(
    str(js_src_dir / "**/tsconfig.tsbuildinfo"), recursive=True
)

# Delete all `dist` folders
for dist_dir in dist_dirs:
    with contextlib.suppress(FileNotFoundError):
        shutil.rmtree(dist_dir)

# Delete all `node_modules` folders
for node_modules_dir in node_modules_dirs:
    with contextlib.suppress(FileNotFoundError):
        shutil.rmtree(node_modules_dir)

# Delete all `tsconfig.tsbuildinfo` files
for tsconfig_tsbuildinfo_file in tsconfig_tsbuildinfo_files:
    with contextlib.suppress(FileNotFoundError):
        os.remove(tsconfig_tsbuildinfo_file)
