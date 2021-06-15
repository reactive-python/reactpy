import logging
import re
from pathlib import Path
from typing import Set, Tuple
from urllib.parse import urlparse

import requests

from idom.config import IDOM_WED_MODULES_DIR


logger = logging.getLogger(__name__)


def web_module_path(name: str) -> Path:
    path = IDOM_WED_MODULES_DIR.current.joinpath(*name.split("/"))
    return path.with_suffix(path.suffix + ".js")


def resolve_module_exports_from_file(file: Path, max_depth: int) -> Set[str]:
    if max_depth == 0:
        logger.warning(f"Did not resolve all exports for {file} - max depth reached")
        return set()
    elif not file.exists():
        logger.warning(f"Did not resolve exports for unknown file {file}")
        return set()

    export_names, references = resolve_module_exports_from_source(file.read_text())

    for ref in references:
        if urlparse(ref).scheme:  # is an absolute URL
            export_names.update(resolve_module_exports_from_url(ref, max_depth - 1))
        else:
            path = _resolve_relative_file_path(file, ref)
            export_names.update(resolve_module_exports_from_file(path, max_depth - 1))

    return export_names


def resolve_module_exports_from_url(url: str, max_depth: int) -> Set[str]:
    if max_depth == 0:
        logger.warning(f"Did not resolve all exports for {url} - max depth reached")
        return set()

    try:
        text = requests.get(url).text
    except requests.exceptions.ConnectionError as error:
        reason = "" if error is None else " - {error.errno}"
        logger.warning("Did not resolve exports for url " + url + reason)
        return set()

    export_names, references = resolve_module_exports_from_source(text)

    for ref in references:
        url = _resolve_relative_url(url, ref)
        export_names.update(resolve_module_exports_from_url(url, max_depth - 1))

    return export_names


def resolve_module_exports_from_source(content: str) -> Tuple[Set[str], Set[str]]:
    names: Set[str] = set()
    references: Set[str] = set()
    for export in _JS_EXPORT_PATTERN.findall(content):
        export = export.rstrip(";").strip()
        # Exporting individual features
        if export.startswith("let "):
            names.update(let.split("=", 1)[0] for let in export[4:].split(","))
        elif export.startswith("function "):
            names.add(export[9:].split("(", 1)[0])
        elif export.startswith("class "):
            names.add(export[6:].split("{", 1)[0])
        # Renaming exports and export list
        elif export.startswith("{") and export.endswith("}"):
            names.update(
                item.split(" as ", 1)[-1] for item in export.strip("{}").split(",")
            )
        # Exporting destructured assignments with renaming
        elif export.startswith("const "):
            names.update(
                item.split(":", 1)[0]
                for item in export[6:].split("=", 1)[0].strip("{}").split(",")
            )
        # Default exports
        elif export.startswith("default "):
            names.add("default")
        # Aggregating modules
        elif export.startswith("* as "):
            names.add(export[5:].split(" from ", 1)[0])
        elif export.startswith("* "):
            references.add(export[2:].split("from ", 1)[-1].strip("'\""))
        elif export.startswith("{") and " from " in export:
            names.update(
                item.split(" as ", 1)[-1]
                for item in export.split(" from ")[0].strip("{}").split(",")
            )
        else:
            logger.warning(f"Unknown export type {export!r}")
    return {n.strip() for n in names}, {r.strip() for r in references}


def _resolve_relative_file_path(base_path: Path, rel_url: str) -> Path:
    if rel_url.startswith("./"):
        return base_path.parent / rel_url[2:]
    while rel_url.startswith("../"):
        base_path = base_path.parent
        rel_url = rel_url[3:]
    return base_path / rel_url


def _resolve_relative_url(base_url: str, rel_url: str) -> str:
    if not rel_url.startswith("."):
        return rel_url
    elif rel_url.startswith("./"):
        return base_url.rsplit("/")[0] + rel_url[1:]
    while rel_url.startswith("../"):
        base_url = base_url.rsplit("/")[0]
        rel_url = rel_url[3:]
    return f"{base_url}/{rel_url}"


_JS_EXPORT_PATTERN = re.compile(r";?\s*export(?=\s+|{)(.*?(?:;|}\s*))", re.MULTILINE)
