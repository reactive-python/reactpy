import json
import sys
from pathlib import Path
from typing import List

import semver


ROOT = Path("__file__").parent.parent
VERSION_FILE = ROOT / Path("VERSION")
PY_PKG_INIT_FILE = ROOT / "src" / "idom" / "__init__.py"
JS_ROOT_DIR = ROOT / "src" / "client"
JS_PACKAGE_JSON_FILES = [
    pkg_dir / "package.json" for pkg_dir in (JS_ROOT_DIR / "packages").iterdir()
] + [JS_ROOT_DIR / "package.json"]

VERSION_INFO = semver.VersionInfo.parse(VERSION_FILE.read_text().strip())


def main(args: List[str]) -> None:
    version_str = str(VERSION_INFO)
    update_py_version(version_str)
    update_js_versions(version_str)


def update_py_version(new_version: str) -> None:
    new_lines = PY_PKG_INIT_FILE.read_text().splitlines()
    for index, line in enumerate(new_lines):
        if line.startswith('__version__ = "') and line.endswith('"  # DO NOT MODIFY'):
            line = f'__version__ = "{new_version}"  # DO NOT MODIFY'
            new_lines[index] = line
            break
    else:
        raise RuntimeError(f"No __version__ assignment found in {PY_PKG_INIT_FILE}")
    PY_PKG_INIT_FILE.write_text("\n".join(new_lines) + "\n")


def update_js_versions(new_version: str) -> None:
    for pkg_json_file in JS_PACKAGE_JSON_FILES:
        pkg_json = json.loads(pkg_json_file.read_text())
        pkg_json["version"] = new_version
        pkg_json_file.write_text(json.dumps(pkg_json, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main(sys.argv)
