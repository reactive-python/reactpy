import json
from pathlib import Path

import semver


ROOT = Path("__file__").parent.parent
VERSION_FILE = ROOT / Path("VERSION")
PY_PKG_INIT_FILE = ROOT / "src" / "idom" / "__init__.py"
JS_ROOT_DIR = ROOT / "src" / "client"
JS_PACKAGE_JSON_FILES = [
    pkg_dir / "package.json" for pkg_dir in (JS_ROOT_DIR / "packages").iterdir()
] + [JS_ROOT_DIR / "package.json"]
CHANGELOG_FILE = ROOT / "docs" / "source" / "about" / "changelog.rst"
VERSION_INFO = semver.VersionInfo.parse(VERSION_FILE.read_text().strip())


def main() -> None:
    version_str = str(VERSION_INFO)
    update_py_version(version_str)
    update_js_versions(version_str)
    update_changelog_version(version_str)


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


def update_changelog_version(new_version: str) -> None:
    old_content = CHANGELOG_FILE.read_text().split("\n")

    new_content = []
    for index in range(0, len(old_content), 2):
        if index == len(old_content) - 2:
            # reached end of file
            continue

        old_lines = old_content[index : index + 2]
        if old_lines[0] == "Unreleased" and old_lines[1] == ("-" * len(old_lines[0])):
            new_content.append(_UNRELEASED_SECTION)
            new_content.append(new_version)
            new_content.append("-" * len(new_version))
            new_content.extend(old_content[index + 2 :])
            break
        else:
            new_content.extend(old_lines)
    else:
        raise ValueError(f"Did not find 'Unreleased' section in {CHANGELOG_FILE}")

    CHANGELOG_FILE.write_text("\n".join(new_content))


_UNRELEASED_SECTION = """\
Unreleased
----------

Nothing yet...

"""


if __name__ == "__main__":
    main()
