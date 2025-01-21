from __future__ import annotations

import sys
from collections.abc import Collection, Iterator
from pathlib import Path

from sphinx.application import Sphinx

HERE = Path(__file__).parent
SRC = HERE.parent.parent.parent / "src"
PYTHON_PACKAGE = SRC / "reactpy"

AUTO_DIR = HERE.parent / "_auto"
AUTO_DIR.mkdir(exist_ok=True)

API_FILE = AUTO_DIR / "apis.rst"

# All valid RST section symbols - it shouldn't be realistically possible to exhaust them
SECTION_SYMBOLS = r"""!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~"""

AUTODOC_TEMPLATE_WITH_MEMBERS = """\
.. automodule:: {module}
    :members:
    :ignore-module-all:
"""

AUTODOC_TEMPLATE_WITHOUT_MEMBERS = """\
.. automodule:: {module}
    :ignore-module-all:
"""

TITLE = """\
==========
Python API
==========
"""


def generate_api_docs():
    content = [TITLE]

    for file in walk_python_files(PYTHON_PACKAGE, ignore_dirs={"__pycache__"}):
        if file.name == "__init__.py":
            if file.parent != PYTHON_PACKAGE:
                content.append(make_package_section(file))
        else:
            content.append(make_module_section(file))

    API_FILE.write_text("\n".join(content))


def make_package_section(file: Path) -> str:
    parent_dir = file.parent
    symbol = get_section_symbol(parent_dir)
    section_name = f"``{parent_dir.name}``"
    module_name = get_module_name(parent_dir)
    return (
        section_name
        + "\n"
        + (symbol * len(section_name))
        + "\n"
        + AUTODOC_TEMPLATE_WITHOUT_MEMBERS.format(module=module_name)
    )


def make_module_section(file: Path) -> str:
    symbol = get_section_symbol(file)
    section_name = f"``{file.stem}``"
    module_name = get_module_name(file)
    return (
        section_name
        + "\n"
        + (symbol * len(section_name))
        + "\n"
        + AUTODOC_TEMPLATE_WITH_MEMBERS.format(module=module_name)
    )


def get_module_name(path: Path) -> str:
    return ".".join(path.with_suffix("").relative_to(PYTHON_PACKAGE.parent).parts)


def get_section_symbol(path: Path) -> str:
    rel_path = path.relative_to(PYTHON_PACKAGE)
    rel_path_parts = rel_path.parts
    if len(rel_path_parts) > len(SECTION_SYMBOLS):
        msg = f"package structure is too deep - ran out of section symbols: {rel_path}"
        raise RuntimeError(msg)
    return SECTION_SYMBOLS[len(rel_path_parts) - 1]


def walk_python_files(root: Path, ignore_dirs: Collection[str]) -> Iterator[Path]:
    """Iterate over Python files

    We yield in a particular order to get the correction title section structure. Given
    a directory structure of the form::

        project/
            __init__.py
            /package
                __init__.py
                module_a.py
            module_b.py

    We yield the files in this order::

        project / __init__.py
        project / package / __init__.py
        project / package / module_a.py
        project / module_b.py

    In this way we generate the section titles in the appropriate order::

        project
        =======

        project.package
        ---------------

        project.package.module_a
        ------------------------

    """
    for path in sorted(
        root.iterdir(),
        key=lambda path: (
            # __init__.py files first
            int(not path.name == "__init__.py"),
            # then directories
            int(not path.is_dir()),
            # sort by file name last
            path.name,
        ),
    ):
        if path.is_dir():
            if (path / "__init__.py").exists() and path.name not in ignore_dirs:
                yield from walk_python_files(path, ignore_dirs)
        elif path.suffix == ".py":
            yield path


def setup(app: Sphinx) -> None:
    if sys.platform == "win32" and sys.version_info[:2] == (3, 7):
        return None
    generate_api_docs()
    return None
