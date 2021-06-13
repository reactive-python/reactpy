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
    export_names, references = resolve_module_exports_from_source(file.read_text())
    if max_depth == 0:
        logger.warning(f"Unable to resolve all exports for {file}")
    else:
        for ref in references:
            if urlparse(ref).scheme:  # is an absolute URL
                export_names.update(resolve_module_exports_from_url(ref, max_depth - 1))
            elif ref.startswith("."):
                path = _resolve_relative_file_path(file, ref)
                export_names.update(
                    resolve_module_exports_from_file(path, max_depth - 1)
                )
            else:
                logger.warning(f"Did not resolve exports for unknown location {ref}")
    return export_names


def resolve_module_exports_from_url(url: str, max_depth: int) -> Set[str]:
    export_names, references = resolve_module_exports_from_source(
        requests.get(url).text
    )
    if max_depth == 0:
        logger.warning(f"Unable to fully resolve all exports for {url}")
    else:
        for ref in references:
            url = _resolve_relative_url(url, ref)
            export_names.update(resolve_module_exports_from_url(url, max_depth - 1))
    return export_names


def resolve_module_exports_from_source(content: str) -> Tuple[Set[str], Set[str]]:
    names: Set[str] = set()
    for match in _JS_MODULE_EXPORT_PATTERN.findall(content):
        for export in match.split(","):
            export_parts = export.split(" as ", 1)
            names.add(export_parts[-1].strip())
    names.update(_JS_MODULE_EXPORT_FUNC_PATTERN.findall(content))
    names.update(_JS_MODULE_EXPORT_NAME_PATTERN.findall(content))

    references: Set[str] = set(_JS_MODULE_EXPORT_FROM_REF_PATTERN.findall(content))
    return names, references


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


_JS_MODULE_EXPORT_PATTERN = re.compile(
    r";?\s*export\s*{([0-9a-zA-Z_$\s,]*)}\s*;", re.MULTILINE
)
_JS_VAR = r"[a-zA-Z_$][0-9a-zA-Z_$]*"
_JS_MODULE_EXPORT_NAME_PATTERN = re.compile(
    fr";?\s*export\s+({_JS_VAR})\s+{_JS_VAR}\s*;", re.MULTILINE
)
_JS_MODULE_EXPORT_FUNC_PATTERN = re.compile(
    fr";?\s*export\s+function\s+({_JS_VAR})\s*\(.*?", re.MULTILINE
)
_JS_MODULE_EXPORT_FROM_REF_PATTERN = re.compile(
    r""";?\s*export\s+\*\s+from\s+['"](.*?)['"];"""
)
