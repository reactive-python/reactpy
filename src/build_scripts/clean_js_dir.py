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
static_output_dir = pathlib.Path(__file__).parent.parent / "reactpy" / "static"

# Delete all `dist` folders
dist_dirs = glob.glob(str(js_src_dir / "**/dist"), recursive=True)
for dist_dir in dist_dirs:
    with contextlib.suppress(FileNotFoundError):
        shutil.rmtree(dist_dir)

# Delete all `node_modules` folders
node_modules_dirs = glob.glob(str(js_src_dir / "**/node_modules"), recursive=True)
for node_modules_dir in node_modules_dirs:
    with contextlib.suppress(FileNotFoundError):
        shutil.rmtree(node_modules_dir)

# Delete all `tsconfig.tsbuildinfo` files
tsconfig_tsbuildinfo_files = glob.glob(
    str(js_src_dir / "**/tsconfig.tsbuildinfo"), recursive=True
)
for tsconfig_tsbuildinfo_file in tsconfig_tsbuildinfo_files:
    with contextlib.suppress(FileNotFoundError):
        os.remove(tsconfig_tsbuildinfo_file)

# Delete all `index-*.js` files
index_js_files = glob.glob(str(static_output_dir / "index-*.js*"))
for index_js_file in index_js_files:
    with contextlib.suppress(FileNotFoundError):
        os.remove(index_js_file)
