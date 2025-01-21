import subprocess
from pathlib import Path

from sphinx.application import Sphinx

SOURCE_DIR = Path(__file__).parent.parent
CUSTOM_JS_DIR = SOURCE_DIR / "_custom_js"


def setup(app: Sphinx) -> None:
    subprocess.run("bun install", cwd=CUSTOM_JS_DIR, shell=True)  # noqa S607
    subprocess.run("bun run build", cwd=CUSTOM_JS_DIR, shell=True)  # noqa S607
