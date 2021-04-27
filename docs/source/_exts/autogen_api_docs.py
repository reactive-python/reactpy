from pathlib import Path

from sphinx.application import Sphinx


HERE = Path(__file__).parent
PACKAGE_SRC = HERE.parent.parent.parent / "src"
PUBLIC_API_REFERENCE_FILE = HERE.parent / "api-reference.rst"
PRIVATE_API_REFERENCE_FILE = HERE.parent / "developer-apis.rst"


PUBLIC_TITLE = """API Reference
=============
"""

PRIVATE_TITLE = """Developer APIs
==============
"""

AUTODOC_TEMPLATE = """
.. automodule:: {module}
    :members:
"""


def make_autodoc_section(module_name: str) -> str:
    return AUTODOC_TEMPLATE.format(module=module_name, underline="-" * len(module_name))


def generate_api_docs():
    public_docs = [PUBLIC_TITLE]
    private_docs = [PRIVATE_TITLE]

    for file in sorted(PACKAGE_SRC.glob("**/*.py")):
        if file.stem.startswith("__"):
            # skip __init__ and __main__
            continue
        rel_path = file.relative_to(PACKAGE_SRC)
        module_name = ".".join(rel_path.with_suffix("").parts)
        api_docs = make_autodoc_section(module_name)
        (private_docs if "._" in module_name else public_docs).append(api_docs)

    PUBLIC_API_REFERENCE_FILE.write_text("\n".join(public_docs))
    PRIVATE_API_REFERENCE_FILE.write_text("\n".join(private_docs))


def setup(app: Sphinx) -> None:
    generate_api_docs()
    return None
