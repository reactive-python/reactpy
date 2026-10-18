"""
Development/debug script to parse pyproject.toml to find dependecies then install them in the local
environment via `uv pip install -U <pkg_names>`
"""

import subprocess
import tomllib as toml
from pathlib import Path

DEPENDENCIES = set()


def find_deps(data):
    """Recurse through all categories and find any list with `dependencies` in the name, then combine
    all dependencies into a single list"""
    if isinstance(data, dict):
        for key, value in data.items():
            if (
                "dependencies" in key
                and isinstance(value, list)
                and value
                and isinstance(value[0], str)
            ):
                DEPENDENCIES.update(value)
            else:
                find_deps(value)
    elif isinstance(data, list):
        for item in data:
            find_deps(item)


def install_deps():
    pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        pyproject_data = toml.load(f)
    find_deps(pyproject_data)
    DEPENDENCIES.discard(
        "ruff"
    )  # ruff only exists in dev dependencies for CI purposes.
    subprocess.run(["uv", "pip", "install", "-U", *DEPENDENCIES], check=False)  # noqa: S607,S603


if __name__ == "__main__":
    install_deps()
