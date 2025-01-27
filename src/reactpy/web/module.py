from __future__ import annotations

import filecmp
import logging
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, NewType, overload

from reactpy.config import REACTPY_DEBUG, REACTPY_WEB_MODULES_DIR
from reactpy.core.vdom import make_vdom_constructor
from reactpy.types import ImportSourceDict, VdomDictConstructor
from reactpy.web.utils import (
    module_name_suffix,
    resolve_module_exports_from_file,
    resolve_module_exports_from_url,
)

logger = logging.getLogger(__name__)

SourceType = NewType("SourceType", str)

NAME_SOURCE = SourceType("NAME")
"""A named source - usually a Javascript package name"""

URL_SOURCE = SourceType("URL")
"""A source loaded from a URL, usually a CDN"""


def module_from_url(
    url: str,
    fallback: Any | None = None,
    resolve_exports: bool | None = None,
    resolve_exports_depth: int = 5,
    unmount_before_update: bool = False,
) -> WebModule:
    """Load a :class:`WebModule` from a :data:`URL_SOURCE`

    Parameters:
        url:
            Where the javascript module will be loaded from which conforms to the
            interface for :ref:`Custom Javascript Components`
        fallback:
            What to temporarily display while the module is being loaded.
        resolve_imports:
            Whether to try and find all the named exports of this module.
        resolve_exports_depth:
            How deeply to search for those exports.
        unmount_before_update:
            Cause the component to be unmounted before each update. This option should
            only be used if the imported package fails to re-render when props change.
            Using this option has negative performance consequences since all DOM
            elements must be changed on each render. See :issue:`461` for more info.
    """
    return WebModule(
        source=url,
        source_type=URL_SOURCE,
        default_fallback=fallback,
        file=None,
        export_names=(
            resolve_module_exports_from_url(url, resolve_exports_depth)
            if (
                resolve_exports
                if resolve_exports is not None
                else REACTPY_DEBUG.current
            )
            else None
        ),
        unmount_before_update=unmount_before_update,
    )


def module_from_file(
    name: str,
    file: str | Path,
    fallback: Any | None = None,
    resolve_exports: bool | None = None,
    resolve_exports_depth: int = 5,
    unmount_before_update: bool = False,
    symlink: bool = False,
) -> WebModule:
    """Load a :class:`WebModule` from a given ``file``

    Parameters:
        name:
            The name of the package
        file:
            The file from which the content of the web module will be created.
        fallback:
            What to temporarily display while the module is being loaded.
        resolve_imports:
            Whether to try and find all the named exports of this module.
        resolve_exports_depth:
            How deeply to search for those exports.
        unmount_before_update:
            Cause the component to be unmounted before each update. This option should
            only be used if the imported package fails to re-render when props change.
            Using this option has negative performance consequences since all DOM
            elements must be changed on each render. See :issue:`461` for more info.
        symlink:
            Whether the web module should be saved as a symlink to the given ``file``.
    """
    name += module_name_suffix(name)

    source_file = Path(file).resolve()
    target_file = _web_module_path(name)
    if not source_file.exists():
        msg = f"Source file does not exist: {source_file}"
        raise FileNotFoundError(msg)

    if not target_file.exists():
        _copy_file(target_file, source_file, symlink)
    elif not _equal_files(source_file, target_file):
        logger.info(
            f"Existing web module {name!r} will "
            f"be replaced with {target_file.resolve()}"
        )
        target_file.unlink()
        _copy_file(target_file, source_file, symlink)

    return WebModule(
        source=name,
        source_type=NAME_SOURCE,
        default_fallback=fallback,
        file=target_file,
        export_names=(
            resolve_module_exports_from_file(source_file, resolve_exports_depth)
            if (
                resolve_exports
                if resolve_exports is not None
                else REACTPY_DEBUG.current
            )
            else None
        ),
        unmount_before_update=unmount_before_update,
    )


def _equal_files(f1: Path, f2: Path) -> bool:
    f1 = f1.resolve()
    f2 = f2.resolve()
    return (
        (f1.is_symlink() or f2.is_symlink()) and (f1.resolve() == f2.resolve())
    ) or filecmp.cmp(str(f1), str(f2), shallow=False)


def _copy_file(target: Path, source: Path, symlink: bool) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if symlink:
        target.symlink_to(source)
    else:
        shutil.copy(source, target)


def module_from_string(
    name: str,
    content: str,
    fallback: Any | None = None,
    resolve_exports: bool | None = None,
    resolve_exports_depth: int = 5,
    unmount_before_update: bool = False,
) -> WebModule:
    """Load a :class:`WebModule` whose ``content`` comes from a string.

    Parameters:
        name:
            The name of the package
        content:
            The contents of the web module
        fallback:
            What to temporarily display while the module is being loaded.
        resolve_imports:
            Whether to try and find all the named exports of this module.
        resolve_exports_depth:
            How deeply to search for those exports.
        unmount_before_update:
            Cause the component to be unmounted before each update. This option should
            only be used if the imported package fails to re-render when props change.
            Using this option has negative performance consequences since all DOM
            elements must be changed on each render. See :issue:`461` for more info.
    """
    name += module_name_suffix(name)

    target_file = _web_module_path(name)

    if target_file.exists() and target_file.read_text(encoding="utf-8") != content:
        logger.info(
            f"Existing web module {name!r} will "
            f"be replaced with {target_file.resolve()}"
        )
        target_file.unlink()

    target_file.parent.mkdir(parents=True, exist_ok=True)
    target_file.write_text(content)

    return WebModule(
        source=name,
        source_type=NAME_SOURCE,
        default_fallback=fallback,
        file=target_file,
        export_names=(
            resolve_module_exports_from_file(target_file, resolve_exports_depth)
            if (
                resolve_exports
                if resolve_exports is not None
                else REACTPY_DEBUG.current
            )
            else None
        ),
        unmount_before_update=unmount_before_update,
    )


@dataclass(frozen=True)
class WebModule:
    source: str
    source_type: SourceType
    default_fallback: Any | None
    export_names: set[str] | None
    file: Path | None
    unmount_before_update: bool


@overload
def export(
    web_module: WebModule,
    export_names: str,
    fallback: Any | None = ...,
    allow_children: bool = ...,
) -> VdomDictConstructor: ...


@overload
def export(
    web_module: WebModule,
    export_names: list[str] | tuple[str, ...],
    fallback: Any | None = ...,
    allow_children: bool = ...,
) -> list[VdomDictConstructor]: ...


def export(
    web_module: WebModule,
    export_names: str | list[str] | tuple[str, ...],
    fallback: Any | None = None,
    allow_children: bool = True,
) -> VdomDictConstructor | list[VdomDictConstructor]:
    """Return one or more VDOM constructors from a :class:`WebModule`

    Parameters:
        export_names:
            One or more names to export. If given as a string, a single component
            will be returned. If a list is given, then a list of components will be
            returned.
        fallback:
            What to temporarily display while the module is being loaded.
        allow_children:
            Whether or not these components can have children.
    """
    if isinstance(export_names, str):
        if (
            web_module.export_names is not None
            and export_names not in web_module.export_names
        ):
            msg = f"{web_module.source!r} does not export {export_names!r}"
            raise ValueError(msg)
        return _make_export(web_module, export_names, fallback, allow_children)
    else:
        if web_module.export_names is not None:
            missing = sorted(set(export_names).difference(web_module.export_names))
            if missing:
                msg = f"{web_module.source!r} does not export {missing!r}"
                raise ValueError(msg)
        return [
            _make_export(web_module, name, fallback, allow_children)
            for name in export_names
        ]


def _make_export(
    web_module: WebModule,
    name: str,
    fallback: Any | None,
    allow_children: bool,
) -> VdomDictConstructor:
    return make_vdom_constructor(
        name,
        allow_children=allow_children,
        import_source=ImportSourceDict(
            source=web_module.source,
            sourceType=web_module.source_type,
            fallback=(fallback or web_module.default_fallback),
            unmountBeforeUpdate=web_module.unmount_before_update,
        ),
    )


def _web_module_path(name: str) -> Path:
    directory = REACTPY_WEB_MODULES_DIR.current
    path = directory.joinpath(*name.split("/"))
    return path.with_suffix(path.suffix)
