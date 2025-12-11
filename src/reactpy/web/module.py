from __future__ import annotations

import filecmp
import hashlib
import logging
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, NewType, overload

from reactpy._warnings import warn
from reactpy.config import REACTPY_DEBUG, REACTPY_WEB_MODULES_DIR
from reactpy.core.vdom import Vdom
from reactpy.types import ImportSourceDict, VdomConstructor
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


_URL_WEB_MODULE_CACHE: dict[str, WebModule] = {}
_FILE_WEB_MODULE_CACHE: dict[str, WebModule] = {}
_STRING_WEB_MODULE_CACHE: dict[str, WebModule] = {}


@overload
def reactjs_component_from_url(
    url: str,
    import_names: str,
    resolve_imports: bool = ...,
    resolve_imports_depth: int = ...,
    fallback: Any | None = ...,
    unmount_before_update: bool = ...,
    allow_children: bool = ...,
) -> VdomConstructor: ...


@overload
def reactjs_component_from_url(
    url: str,
    import_names: list[str] | tuple[str, ...],
    resolve_imports: bool = ...,
    resolve_imports_depth: int = ...,
    fallback: Any | None = ...,
    unmount_before_update: bool = ...,
    allow_children: bool = ...,
) -> list[VdomConstructor]: ...


def reactjs_component_from_url(
    url: str,
    import_names: str | list[str] | tuple[str, ...],
    resolve_imports: bool = True,
    resolve_imports_depth: int = 5,
    fallback: Any | None = None,
    unmount_before_update: bool = False,
    allow_children: bool = True,
) -> VdomConstructor | list[VdomConstructor]:
    """Import a component from a URL.

    Parameters:
        url:
            The URL to import the component from.
        import_names:
            One or more component names to import. If given as a string, a single component
            will be returned. If a list is given, then a list of components will be
            returned.
        resolve_imports:
            Whether to try and find all the named imports of this module.
        resolve_imports_depth:
            How deeply to search for those imports.
        fallback:
            What to temporarily display while the module is being loaded.
        unmount_before_update:
            Cause the component to be unmounted before each update. This option should
            only be used if the imported package fails to re-render when props change.
            Using this option has negative performance consequences since all DOM
            elements must be changed on each render. See :issue:`461` for more info.
        allow_children:
            Whether or not these components can have children.
    """
    key = f"{url}{resolve_imports}{resolve_imports_depth}{unmount_before_update}"
    if key in _URL_WEB_MODULE_CACHE:
        module = _URL_WEB_MODULE_CACHE[key]
    else:
        module = _module_from_url(
            url,
            fallback=fallback,
            resolve_imports=resolve_imports,
            resolve_imports_depth=resolve_imports_depth,
            unmount_before_update=unmount_before_update,
        )
        _URL_WEB_MODULE_CACHE[key] = module
    return _vdom_from_web_module(module, import_names, fallback, allow_children)


@overload
def reactjs_component_from_npm(
    package: str,
    import_names: str,
    resolve_imports: bool = ...,
    resolve_imports_depth: int = ...,
    version: str = "latest",
    cdn: str = "https://esm.sh",
    fallback: Any | None = ...,
    unmount_before_update: bool = ...,
    allow_children: bool = ...,
) -> VdomConstructor: ...


@overload
def reactjs_component_from_npm(
    package: str,
    import_names: list[str] | tuple[str, ...],
    resolve_imports: bool = ...,
    resolve_imports_depth: int = ...,
    version: str = "latest",
    cdn: str = "https://esm.sh",
    fallback: Any | None = ...,
    unmount_before_update: bool = ...,
    allow_children: bool = ...,
) -> list[VdomConstructor]: ...


def reactjs_component_from_npm(
    package: str,
    import_names: str | list[str] | tuple[str, ...],
    resolve_imports: bool = True,
    resolve_imports_depth: int = 5,
    version: str = "latest",
    cdn: str = "https://esm.sh",
    fallback: Any | None = None,
    unmount_before_update: bool = False,
    allow_children: bool = True,
) -> VdomConstructor | list[VdomConstructor]:
    """Import a component from an NPM package.

    Parameters:
        package:
            The name of the NPM package.
        import_names:
            One or more component names to import. If given as a string, a single component
            will be returned. If a list is given, then a list of components will be
            returned.
        resolve_imports:
            Whether to try and find all the named imports of this module.
        resolve_imports_depth:
            How deeply to search for those imports.
        version:
            The version of the package to use. Defaults to "latest".
        cdn:
            The CDN to use. Defaults to "https://esm.sh".
        fallback:
            What to temporarily display while the module is being loaded.
        unmount_before_update:
            Cause the component to be unmounted before each update. This option should
            only be used if the imported package fails to re-render when props change.
            Using this option has negative performance consequences since all DOM
            elements must be changed on each render. See :issue:`461` for more info.
        allow_children:
            Whether or not these components can have children.
    """
    url = f"{cdn}/{package}@{version}"

    if "esm.sh" in cdn:
        if "?" in url:
            url += "&external=react,react-dom"
        else:
            url += "?external=react,react-dom"

    return reactjs_component_from_url(
        url,
        import_names,
        fallback=fallback,
        resolve_imports=resolve_imports,
        resolve_imports_depth=resolve_imports_depth,
        unmount_before_update=unmount_before_update,
        allow_children=allow_children,
    )


@overload
def reactjs_component_from_file(
    file: str | Path,
    import_names: str,
    resolve_imports: bool = ...,
    resolve_imports_depth: int = ...,
    name: str = "",
    fallback: Any | None = ...,
    unmount_before_update: bool = ...,
    symlink: bool = ...,
    allow_children: bool = ...,
) -> VdomConstructor: ...


@overload
def reactjs_component_from_file(
    file: str | Path,
    import_names: list[str] | tuple[str, ...],
    resolve_imports: bool = ...,
    resolve_imports_depth: int = ...,
    name: str = "",
    fallback: Any | None = ...,
    unmount_before_update: bool = ...,
    symlink: bool = ...,
    allow_children: bool = ...,
) -> list[VdomConstructor]: ...


def reactjs_component_from_file(
    file: str | Path,
    import_names: str | list[str] | tuple[str, ...],
    resolve_imports: bool = True,
    resolve_imports_depth: int = 5,
    name: str = "",
    fallback: Any | None = None,
    unmount_before_update: bool = False,
    symlink: bool = False,
    allow_children: bool = True,
) -> VdomConstructor | list[VdomConstructor]:
    """Import a component from a file.

    Parameters:
        file:
            The file from which the content of the web module will be created.
        import_names:
            One or more component names to import. If given as a string, a single component
            will be returned. If a list is given, then a list of components will be
            returned.
        resolve_imports:
            Whether to try and find all the named imports of this module.
        resolve_imports_depth:
            How deeply to search for those imports.
        name:
            The human-readable name of the ReactJS package
        fallback:
            What to temporarily display while the module is being loaded.
        unmount_before_update:
            Cause the component to be unmounted before each update. This option should
            only be used if the imported package fails to re-render when props change.
            Using this option has negative performance consequences since all DOM
            elements must be changed on each render. See :issue:`461` for more info.
        symlink:
            Whether the web module should be saved as a symlink to the given ``file``.
        allow_children:
            Whether or not these components can have children.
    """
    name = name or hashlib.sha256(str(file).encode()).hexdigest()[:10]
    key = f"{name}{resolve_imports}{resolve_imports_depth}{unmount_before_update}"
    if key in _FILE_WEB_MODULE_CACHE:
        module = _FILE_WEB_MODULE_CACHE[key]
    else:
        module = _module_from_file(
            name,
            file,
            fallback=fallback,
            resolve_imports=resolve_imports,
            resolve_imports_depth=resolve_imports_depth,
            unmount_before_update=unmount_before_update,
            symlink=symlink,
        )
        _FILE_WEB_MODULE_CACHE[key] = module
    return _vdom_from_web_module(module, import_names, fallback, allow_children)


@overload
def reactjs_component_from_string(
    content: str,
    import_names: str,
    resolve_imports: bool = ...,
    resolve_imports_depth: int = ...,
    name: str = "",
    fallback: Any | None = ...,
    unmount_before_update: bool = ...,
    allow_children: bool = ...,
) -> VdomConstructor: ...


@overload
def reactjs_component_from_string(
    content: str,
    import_names: list[str] | tuple[str, ...],
    resolve_imports: bool = ...,
    resolve_imports_depth: int = ...,
    name: str = "",
    fallback: Any | None = ...,
    unmount_before_update: bool = ...,
    allow_children: bool = ...,
) -> list[VdomConstructor]: ...


def reactjs_component_from_string(
    content: str,
    import_names: str | list[str] | tuple[str, ...],
    resolve_imports: bool = True,
    resolve_imports_depth: int = 5,
    name: str = "",
    fallback: Any | None = None,
    unmount_before_update: bool = False,
    allow_children: bool = True,
) -> VdomConstructor | list[VdomConstructor]:
    """Import a component from a string.

    Parameters:
        content:
            The contents of the web module
        import_names:
            One or more component names to import. If given as a string, a single component
            will be returned. If a list is given, then a list of components will be
            returned.
        resolve_imports:
            Whether to try and find all the named imports of this module.
        resolve_imports_depth:
            How deeply to search for those imports.
        name:
            The human-readable name of the ReactJS package
        fallback:
            What to temporarily display while the module is being loaded.
        unmount_before_update:
            Cause the component to be unmounted before each update. This option should
            only be used if the imported package fails to re-render when props change.
            Using this option has negative performance consequences since all DOM
            elements must be changed on each render. See :issue:`461` for more info.
        allow_children:
            Whether or not these components can have children.
    """
    name = name or hashlib.sha256(content.encode()).hexdigest()[:10]
    key = f"{name}{resolve_imports}{resolve_imports_depth}{unmount_before_update}"
    if key in _STRING_WEB_MODULE_CACHE:
        module = _STRING_WEB_MODULE_CACHE[key]
    else:
        module = _module_from_string(
            name,
            content,
            fallback=fallback,
            resolve_imports=resolve_imports,
            resolve_imports_depth=resolve_imports_depth,
            unmount_before_update=unmount_before_update,
        )
        _STRING_WEB_MODULE_CACHE[key] = module
    return _vdom_from_web_module(module, import_names, fallback, allow_children)


def module_from_url(
    url: str,
    fallback: Any | None = None,
    resolve_exports: bool = False,
    resolve_exports_depth: int = 5,
    unmount_before_update: bool = False,
) -> WebModule:  # pragma: no cover
    warn(
        "module_from_url is deprecated, use reactjs_component_from_url instead",
        DeprecationWarning,
    )
    return _module_from_url(
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
        "module_from_file is deprecated, use reactjs_component_from_file instead",
        DeprecationWarning,
    )
    return _module_from_file(
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
        "module_from_string is deprecated, use reactjs_component_from_string instead",
        DeprecationWarning,
    )
    return _module_from_string(
        name,
        content,
        fallback=fallback,
        resolve_imports=resolve_exports,
        resolve_imports_depth=resolve_exports_depth,
        unmount_before_update=unmount_before_update,
    )


def _module_from_url(
    url: str,
    fallback: Any | None = None,
    resolve_imports: bool = True,
    resolve_imports_depth: int = 5,
    unmount_before_update: bool = False,
) -> WebModule:
    return WebModule(
        source=url,
        source_type=URL_SOURCE,
        default_fallback=fallback,
        file=None,
        export_names=(
            resolve_module_exports_from_url(url, resolve_imports_depth)
            if (
                resolve_imports
                if resolve_imports is not None
                else REACTPY_DEBUG.current
            )
            else None
        ),
        unmount_before_update=unmount_before_update,
    )


def _module_from_file(
    name: str,
    file: str | Path,
    fallback: Any | None = None,
    resolve_imports: bool = True,
    resolve_imports_depth: int = 5,
    unmount_before_update: bool = False,
    symlink: bool = False,
) -> WebModule:
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
            resolve_module_exports_from_file(source_file, resolve_imports_depth)
            if (
                resolve_imports
                if resolve_imports is not None
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


def _module_from_string(
    name: str,
    content: str,
    fallback: Any | None = None,
    resolve_imports: bool = True,
    resolve_imports_depth: int = 5,
    unmount_before_update: bool = False,
) -> WebModule:
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
            resolve_module_exports_from_file(target_file, resolve_imports_depth)
            if (
                resolve_imports
                if resolve_imports is not None
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
        "export is deprecated, use reactjs_component_from_* functions instead",
        DeprecationWarning,
    )
    return _vdom_from_web_module(web_module, export_names, fallback, allow_children)


def _vdom_from_web_module(
    web_module: WebModule,
    export_names: str | list[str] | tuple[str, ...],
    fallback: Any | None = None,
    allow_children: bool = True,
) -> VdomConstructor | list[VdomConstructor]:
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
            and export_names.split(".")[0] not in web_module.export_names
        ):
            msg = f"{web_module.source!r} does not export {export_names!r}"
            raise ValueError(msg)
        return _make_export(web_module, export_names, fallback, allow_children)
    else:
        if web_module.export_names is not None:
            missing = sorted(
                {e.split(".")[0] for e in export_names}.difference(
                    web_module.export_names
                )
            )
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
) -> VdomConstructor:
    return Vdom(
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
