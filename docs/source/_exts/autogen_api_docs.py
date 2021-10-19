from __future__ import annotations

import sys
from pathlib import Path

from sphinx.application import Sphinx


HERE = Path(__file__).parent
PACKAGE_SRC = HERE.parent.parent.parent / "src"

REFERENCES_DIR = HERE.parent / "references"
REFERENCES_DIR.mkdir(exist_ok=True)

PUBLIC_API_REFERENCE_FILE = REFERENCES_DIR / "user-apis.rst"
PRIVATE_API_REFERENCE_FILE = REFERENCES_DIR / "developer-apis.rst"


PUBLIC_TITLE = "User API\n=============\n"
PUBLIC_MISC_TITLE = "Misc Modules\n------------\n"
PRIVATE_TITLE = "Developer API\n==============\n"
PRIVATE_MISC_TITLE = "Misc Dev Modules\n----------------\n"

AUTODOC_TEMPLATE = ".. automodule:: {module}\n    :members:\n"


def generate_api_docs():
    docs = {
        "public.main": [PUBLIC_TITLE],
        "public.misc": [PUBLIC_MISC_TITLE],
        "private.main": [PRIVATE_TITLE],
        "private.misc": [PRIVATE_MISC_TITLE],
    }

    for file in sorted(pathlib_walk(PACKAGE_SRC, ignore_dirs=["node_modules"])):
        if not file.suffix == ".py" or file.stem.startswith("__"):
            # skip non-Python files along with __init__ and __main__
            continue
        public_vs_private = "private" if is_private_module(file) else "public"
        main_vs_misc = "main" if file_starts_with_docstring(file) else "misc"
        key = f"{public_vs_private}.{main_vs_misc}"
        docs[key].append(make_autodoc_section(file, public_vs_private == "private"))

    public_content = docs["public.main"]
    if len(docs["public.misc"]) > 1:
        public_content += docs["public.misc"]

    private_content = docs["private.main"]
    if len(docs["private.misc"]) > 1:
        private_content += docs["private.misc"]

    PUBLIC_API_REFERENCE_FILE.write_text("\n".join(public_content))
    PRIVATE_API_REFERENCE_FILE.write_text("\n".join(private_content))


def pathlib_walk(root: Path, ignore_dirs: list[str]):
    for path in root.iterdir():
        if path.is_dir():
            if path.name in ignore_dirs:
                continue
            yield from pathlib_walk(path, ignore_dirs)
        else:
            yield path


def is_private_module(path: Path) -> bool:
    return any(p.startswith("_") for p in path.parts)


def make_autodoc_section(path: Path, is_public) -> str:
    rel_path = path.relative_to(PACKAGE_SRC)
    module_name = ".".join(rel_path.with_suffix("").parts)
    return AUTODOC_TEMPLATE.format(module=module_name, underline="-" * len(module_name))


def file_starts_with_docstring(path: Path) -> bool:
    for line in path.read_text().split("\n"):
        if line.startswith("#"):
            continue
        if line.startswith('"""') or line.startswith("'''"):
            return True
        else:
            break
    return False


def setup(app: Sphinx) -> None:
    if sys.platform == "win32" and sys.version_info[:2] == (3, 7):
        return None
    generate_api_docs()
    return None
