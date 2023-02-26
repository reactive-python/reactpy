import json
from datetime import datetime
from pathlib import Path

import semver


ROOT = Path("__file__").parent.parent
VERSION_FILE = ROOT / Path("VERSION")
PY_PKG_INIT_FILE = ROOT / "src" / "reactpy" / "__init__.py"
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
    today = datetime.now().strftime("%Y-%m-%d")
    old_content = CHANGELOG_FILE.read_text().split("\n")

    new_content = []
    for index in range(len(old_content) - 1):
        if index == len(old_content) - 2:
            # reached end of file
            continue

        this_line, next_line = old_content[index : index + 2]
        if this_line == "Unreleased" and next_line == ("-" * len(this_line)):
            new_content.append(_UNRELEASED_SECTION)

            title = f"v{new_version}"
            new_content.append(title)
            new_content.append("-" * len(title))
            new_content.append(f":octicon:`milestone` *released on {today}*")

            new_content.extend(old_content[index + 2 :])
            break
        else:
            new_content.append(this_line)
    else:
        raise ValueError(f"Did not find 'Unreleased' section in {CHANGELOG_FILE}")

    CHANGELOG_FILE.write_text("\n".join(new_content))


_UNRELEASED_SECTION = """\
Unreleased
----------

No changes.

"""


if __name__ == "__main__":
    main()
