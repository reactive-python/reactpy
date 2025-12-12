import filecmp
import logging
import os
import re
import shutil
import time
from contextlib import contextmanager, suppress
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse, urlunparse

import requests

logger = logging.getLogger(__name__)


def module_name_suffix(name: str) -> str:
    if name.startswith("@"):
        name = name[1:]
    head, _, tail = name.partition("@")  # handle version identifier
    _, _, tail = tail.partition("/")  # get section after version
    return PurePosixPath(tail or head).suffix or ".js"


def resolve_from_module_file(
    file: Path,
    max_depth: int,
    is_regex_import: bool = False,
) -> set[str]:
    if max_depth == 0:
        logger.warning(f"Did not resolve all imports for {file} - max depth reached")
        return set()
    elif not file.exists():
        logger.warning(f"Did not resolve imports for unknown file {file}")
        return set()

    names, references = resolve_from_module_source(
        file.read_text(encoding="utf-8"), exclude_default=is_regex_import
    )

    for ref in references:
        if urlparse(ref).scheme:  # is an absolute URL
            names.update(
                resolve_from_module_url(ref, max_depth - 1, is_regex_import=True)
            )
        else:
            path = file.parent.joinpath(*ref.split("/"))
            names.update(
                resolve_from_module_file(path, max_depth - 1, is_regex_import=True)
            )

    return names


def resolve_from_module_url(
    url: str,
    max_depth: int,
    is_regex_import: bool = False,
) -> set[str]:
    if max_depth == 0:
        logger.warning(f"Did not resolve all imports for {url} - max depth reached")
        return set()

    try:
        text = requests.get(url, timeout=5).text
    except requests.exceptions.ConnectionError as error:
        reason = "" if error is None else " - {error.errno}"
        logger.warning(f"Did not resolve imports for url {url} {reason}")
        return set()

    names, references = resolve_from_module_source(
        text, exclude_default=is_regex_import
    )

    for ref in references:
        url = normalize_url_path(url, ref)
        names.update(resolve_from_module_url(url, max_depth - 1, is_regex_import=True))

    return names


def resolve_from_module_source(
    content: str, exclude_default: bool
) -> tuple[set[str], set[str]]:
    """Find names exported by the given JavaScript module content to assist with ReactPy import resolution.

    Parmeters:
        content: The content of the JavaScript module.
    Returns:
        A tuple where the first item is a set of exported names and the second item is a set of
        referenced module paths.
    """
    all_names: set[str] = set()
    references: set[str] = set()

    if _JS_DEFAULT_EXPORT_PATTERN.search(content):
        all_names.add("default")

    # Exporting functions and classes
    all_names.update(_JS_FUNC_OR_CLS_EXPORT_PATTERN.findall(content))

    for name in _JS_GENERAL_EXPORT_PATTERN.findall(content):
        name = name.rstrip(";").strip()
        # Exporting individual features
        if name.startswith("let "):
            all_names.update(let.split("=", 1)[0] for let in name[4:].split(","))
        # Renaming exports and export list
        elif name.startswith("{") and name.endswith("}"):
            all_names.update(
                item.split(" as ", 1)[-1] for item in name.strip("{}").split(",")
            )
        # Exporting destructured assignments with renaming
        elif name.startswith("const "):
            all_names.update(
                item.split(":", 1)[0]
                for item in name[6:].split("=", 1)[0].strip("{}").split(",")
            )
        # Default exports
        elif name.startswith("default "):
            all_names.add("default")
        # Aggregating modules
        elif name.startswith("* as "):
            all_names.add(name[5:].split(" from ", 1)[0])
        elif name.startswith("* "):
            references.add(name[2:].split("from ", 1)[-1].strip("'\""))
        elif name.startswith("{") and " from " in name:
            all_names.update(
                item.split(" as ", 1)[-1]
                for item in name.split(" from ")[0].strip("{}").split(",")
            )
        elif not (name.startswith("function ") or name.startswith("class ")):
            logger.warning(f"Found unknown export type {name!r}")

    all_names = {n.strip() for n in all_names}
    references = {r.strip() for r in references}

    if exclude_default and "default" in all_names:
        all_names.remove("default")

    return all_names, references


def normalize_url_path(base_url: str, rel_url: str) -> str:
    if not rel_url.startswith("."):
        if rel_url.startswith("/"):
            # copy scheme and hostname from base_url
            return urlunparse(urlparse(base_url)[:2] + urlparse(rel_url)[2:])
        else:
            return rel_url

    base_url = base_url.rsplit("/", 1)[0]

    if rel_url.startswith("./"):
        return base_url + rel_url[1:]

    while rel_url.startswith("../"):
        base_url = base_url.rsplit("/", 1)[0]
        rel_url = rel_url[3:]

    return f"{base_url}/{rel_url}"


def are_files_identical(f1: Path, f2: Path) -> bool:
    f1 = f1.resolve()
    f2 = f2.resolve()
    return (
        (f1.is_symlink() or f2.is_symlink()) and (f1.resolve() == f2.resolve())
    ) or filecmp.cmp(str(f1), str(f2), shallow=False)


def copy_file(target: Path, source: Path, symlink: bool) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if symlink:
        if target.exists():
            target.unlink()
        target.symlink_to(source)
    else:
        temp_target = target.with_suffix(target.suffix + ".tmp")
        shutil.copy(source, temp_target)
        try:
            temp_target.replace(target)
        except OSError:
            # On Windows, replace might fail if the file is open
            # Retry once after a short delay
            time.sleep(0.1)
            try:
                temp_target.replace(target)
            except OSError:
                # If it still fails, try to unlink and rename
                # This is not atomic, but it's a fallback
                if target.exists():
                    target.unlink()
                temp_target.rename(target)


_JS_DEFAULT_EXPORT_PATTERN = re.compile(
    r";?\s*export\s+default\s",
)
_JS_FUNC_OR_CLS_EXPORT_PATTERN = re.compile(
    r";?\s*export\s+(?:function|class)\s+([a-zA-Z_$][0-9a-zA-Z_$]*)"
)
_JS_GENERAL_EXPORT_PATTERN = re.compile(
    r"(?:^|;|})\s*export(?=\s+|{)(.*?)(?=;|$)", re.MULTILINE
)


@contextmanager
def simple_file_lock(lock_file: Path, timeout: float = 10.0):
    start_time = time.time()
    while True:
        try:
            fd = os.open(lock_file, os.O_CREAT | os.O_EXCL | os.O_RDWR)
            os.close(fd)
            break
        except OSError as e:
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Could not acquire lock {lock_file}") from e
            time.sleep(0.1)
    try:
        yield
    finally:
        with suppress(OSError):
            os.unlink(lock_file)
