from __future__ import annotations

from pathlib import Path
from typing import Any, overload

from reactpy._warnings import warn
from reactpy.reactjs.types import (
    NAME_SOURCE,
    URL_SOURCE,
    SourceType,
)
from reactpy.types import JavaScriptModule as WebModule
from reactpy.types import VdomConstructor

# Re-export for backward compatibility
__all__ = [
    "NAME_SOURCE",
    "URL_SOURCE",
    "SourceType",
    "WebModule",
    "export",
    "module_from_file",
    "module_from_string",
    "module_from_url",
]


def module_from_url(
    url: str,
    fallback: Any | None = None,
    resolve_exports: bool = False,
    resolve_exports_depth: int = 5,
    unmount_before_update: bool = False,
) -> WebModule:  # pragma: no cover
    warn(
        "module_from_url is deprecated, use component_from_url instead",
        DeprecationWarning,
    )
    from reactpy.reactjs.module import url_to_module

    return url_to_module(
        url,
        fallback=fallback,
        resolve_imports=resolve_exports,
        resolve_imports_depth=resolve_exports_depth,
        unmount_before_update=unmount_before_update,
    )


def module_from_file(
    name: str,
    file: str | Path,
    fallback: Any | None = None,
    resolve_exports: bool = False,
    resolve_exports_depth: int = 5,
    unmount_before_update: bool = False,
    symlink: bool = False,
) -> WebModule:  # pragma: no cover
    warn(
        "module_from_file is deprecated, use component_from_file instead",
        DeprecationWarning,
    )
    from reactpy.reactjs.module import file_to_module

    return file_to_module(
        name,
        file,
        fallback=fallback,
        resolve_imports=resolve_exports,
        resolve_imports_depth=resolve_exports_depth,
        unmount_before_update=unmount_before_update,
        symlink=symlink,
    )


def module_from_string(
    name: str,
    content: str,
    fallback: Any | None = None,
    resolve_exports: bool = False,
    resolve_exports_depth: int = 5,
    unmount_before_update: bool = False,
) -> WebModule:  # pragma: no cover
    warn(
        "module_from_string is deprecated, use component_from_string instead",
        DeprecationWarning,
    )
    from reactpy.reactjs.module import string_to_module

    return string_to_module(
        name,
        content,
        fallback=fallback,
        resolve_imports=resolve_exports,
        resolve_imports_depth=resolve_exports_depth,
        unmount_before_update=unmount_before_update,
    )


@overload
def export(
    web_module: WebModule,
    export_names: str,
    fallback: Any | None = ...,
    allow_children: bool = ...,
) -> VdomConstructor: ...


@overload
def export(
    web_module: WebModule,
    export_names: list[str] | tuple[str, ...],
    fallback: Any | None = ...,
    allow_children: bool = ...,
) -> list[VdomConstructor]: ...


def export(
    web_module: WebModule,
    export_names: str | list[str] | tuple[str, ...],
    fallback: Any | None = None,
    allow_children: bool = True,
) -> VdomConstructor | list[VdomConstructor]:  # pragma: no cover
    warn(
        "export is deprecated, use component_from_* functions instead",
        DeprecationWarning,
    )
    from reactpy.reactjs.module import module_to_vdom

    return module_to_vdom(web_module, export_names, fallback, allow_children)
