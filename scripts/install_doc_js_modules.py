from pathlib import Path

from idom.client.build_config import find_build_config_item_in_python_file
from idom.client.manage import build, build_config


DOCS_PATH = Path(__file__).parent.parent / "docs"


def install_doc_js_modules():
    config_item = find_build_config_item_in_python_file(
        "__main__", DOCS_PATH / "main.py"
    )
    if (
        config_item is not None
        and config_item["source_name"] not in build_config().config["by_source"]
    ):
        build([config_item])


if __name__ == "__main__":
    install_doc_js_modules()
