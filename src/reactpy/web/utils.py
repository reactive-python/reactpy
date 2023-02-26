import logging
import re
from pathlib import Path, PurePosixPath
from typing import Set, Tuple
from urllib.parse import urlparse

import requests


logger = logging.getLogger(__name__)


def module_name_suffix(name: str) -> str:
    if name.startswith("@"):
        name = name[1:]
    head, _, tail = name.partition("@")  # handle version identifier
    version, _, tail = tail.partition("/")  # get section after version
    return PurePosixPath(tail or head).suffix or ".js"


def resolve_module_exports_from_file(
    file: Path,
    max_depth: int,
    is_re_export: bool = False,
) -> Set[str]:
    if max_depth == 0:
        logger.warning(f"Did not resolve all exports for {file} - max depth reached")
        return set()
    elif not file.exists():
        logger.warning(f"Did not resolve exports for unknown file {file}")
        return set()

    export_names, references = resolve_module_exports_from_source(
        file.read_text(), exclude_default=is_re_export
    )

    for ref in references:
        if urlparse(ref).scheme:  # is an absolute URL
            export_names.update(
                resolve_module_exports_from_url(ref, max_depth - 1, is_re_export=True)
            )
        else:
            path = file.parent.joinpath(*ref.split("/"))
            export_names.update(
                resolve_module_exports_from_file(path, max_depth - 1, is_re_export=True)
            )

    return export_names


def resolve_module_exports_from_url(
    url: str,
    max_depth: int,
    is_re_export: bool = False,
) -> Set[str]:
    if max_depth == 0:
        logger.warning(f"Did not resolve all exports for {url} - max depth reached")
        return set()

    try:
        text = requests.get(url).text
    except requests.exceptions.ConnectionError as error:
        reason = "" if error is None else " - {error.errno}"
        logger.warning("Did not resolve exports for url " + url + reason)
        return set()

    export_names, references = resolve_module_exports_from_source(
        text, exclude_default=is_re_export
    )

    for ref in references:
        url = _resolve_relative_url(url, ref)
        export_names.update(
            resolve_module_exports_from_url(url, max_depth - 1, is_re_export=True)
        )

    return export_names


def resolve_module_exports_from_source(
    content: str, exclude_default: bool
) -> Tuple[Set[str], Set[str]]:
    names: Set[str] = set()
    references: Set[str] = set()

    if _JS_DEFAULT_EXPORT_PATTERN.search(content):
        names.add("default")

    # Exporting functions and classes
    names.update(_JS_FUNC_OR_CLS_EXPORT_PATTERN.findall(content))

    for export in _JS_GENERAL_EXPORT_PATTERN.findall(content):
        export = export.rstrip(";").strip()
        # Exporting individual features
        if export.startswith("let "):
            names.update(let.split("=", 1)[0] for let in export[4:].split(","))
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
        elif not (export.startswith("function ") or export.startswith("class ")):
            logger.warning(f"Unknown export type {export!r}")

    names = {n.strip() for n in names}
    references = {r.strip() for r in references}

    if exclude_default and "default" in names:
        names.remove("default")

    return names, references


def _resolve_relative_url(base_url: str, rel_url: str) -> str:
    if not rel_url.startswith("."):
        return rel_url

    base_url = base_url.rsplit("/", 1)[0]

    if rel_url.startswith("./"):
        return base_url + rel_url[1:]

    while rel_url.startswith("../"):
        base_url = base_url.rsplit("/", 1)[0]
        rel_url = rel_url[3:]

    return f"{base_url}/{rel_url}"


_JS_DEFAULT_EXPORT_PATTERN = re.compile(
    r";?\s*export\s+default\s",
)
_JS_FUNC_OR_CLS_EXPORT_PATTERN = re.compile(
    r";?\s*export\s+(?:function|class)\s+([a-zA-Z_$][0-9a-zA-Z_$]*)"
)
_JS_GENERAL_EXPORT_PATTERN = re.compile(
    r"(?:^|;|})\s*export(?=\s+|{)(.*?)(?=;|$)", re.MULTILINE
)
