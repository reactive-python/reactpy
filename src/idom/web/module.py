"""
Web Modules
===========
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import Any, List, NewType, Optional, Set, Tuple, Union, overload

from idom.config import IDOM_DEBUG_MODE, IDOM_WED_MODULES_DIR
from idom.core.vdom import ImportSourceDict, VdomDictConstructor, make_vdom_constructor

from .utils import (
    module_name_suffix,
    resolve_module_exports_from_file,
    resolve_module_exports_from_url,
)


SourceType = NewType("SourceType", str)

NAME_SOURCE = SourceType("NAME")
"""A named souce - usually a Javascript package name"""

URL_SOURCE = SourceType("URL")
"""A source loaded from a URL, usually from a CDN"""


def module_from_url(
    url: str,
    fallback: Optional[Any] = None,
    resolve_exports: bool = IDOM_DEBUG_MODE.current,
    resolve_exports_depth: int = 5,
) -> WebModule:
    return WebModule(
        source=url,
        source_type=URL_SOURCE,
        default_fallback=fallback,
        file=None,
        export_names=(
            resolve_module_exports_from_url(url, resolve_exports_depth)
            if resolve_exports
            else None
        ),
    )


def module_from_template(
    template: str,
    name: str,
    cdn: str = "https://esm.sh",
    fallback: Optional[Any] = None,
    resolve_exports: bool = IDOM_DEBUG_MODE.current,
    resolve_exports_depth: int = 5,
) -> WebModule:
    cdn = cdn.rstrip("/")

    template_file_name = f"{template}{module_name_suffix(name)}"
    template_file = Path(__file__).parent / "templates" / template_file_name
    if not template_file.exists():
        raise ValueError(f"No template for {template_file_name!r} exists")

    target_file = _web_module_path(name)
    if not target_file.exists():
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_text(
            template_file.read_text().replace("$PACKAGE", name).replace("$CDN", cdn)
        )

    return WebModule(
        source=name + module_name_suffix(name),
        source_type=NAME_SOURCE,
        default_fallback=fallback,
        file=target_file,
        export_names=(
            resolve_module_exports_from_url(f"{cdn}/{name}", resolve_exports_depth)
            if resolve_exports
            else None
        ),
    )


def module_from_file(
    name: str,
    file: Union[str, Path],
    fallback: Optional[Any] = None,
    resolve_exports: bool = IDOM_DEBUG_MODE.current,
    resolve_exports_depth: int = 5,
    symlink: bool = False,
) -> WebModule:
    source_file = Path(file)
    target_file = _web_module_path(name)
    if not source_file.exists():
        raise FileNotFoundError(f"Source file does not exist: {source_file}")
    elif target_file.exists() or target_file.is_symlink():
        raise FileExistsError(f"{name!r} already exists as {target_file.resolve()}")
    else:
        target_file.parent.mkdir(parents=True, exist_ok=True)
        if symlink:
            target_file.symlink_to(source_file)
        else:
            shutil.copy(source_file, target_file)
    return WebModule(
        source=name + module_name_suffix(name),
        source_type=NAME_SOURCE,
        default_fallback=fallback,
        file=target_file,
        export_names=(
            resolve_module_exports_from_file(source_file, resolve_exports_depth)
            if resolve_exports
            else None
        ),
    )


@dataclass(frozen=True)
class WebModule:
    source: str
    source_type: SourceType
    default_fallback: Optional[Any]
    export_names: Optional[Set[str]]
    file: Optional[Path]


@overload
def export(
    web_module: WebModule,
    export_names: str,
    fallback: Optional[Any],
    allow_children: bool,
) -> VdomDictConstructor:
    ...


@overload
def export(
    web_module: WebModule,
    export_names: Union[List[str], Tuple[str]],
    fallback: Optional[Any],
    allow_children: bool,
) -> List[VdomDictConstructor]:
    ...


def export(
    web_module: WebModule,
    export_names: Union[str, List[str], Tuple[str]],
    fallback: Optional[Any] = None,
    allow_children: bool = True,
) -> Union[VdomDictConstructor, List[VdomDictConstructor]]:
    if isinstance(export_names, str):
        if (
            web_module.export_names is not None
            and export_names not in web_module.export_names
        ):
            raise ValueError(f"{web_module.source!r} does not export {export_names!r}")
        return _make_export(web_module, export_names, fallback, allow_children)
    else:
        if web_module.export_names is not None:
            missing = list(
                sorted(set(export_names).difference(web_module.export_names))
            )
            if missing:
                raise ValueError(f"{web_module.source!r} does not export {missing!r}")
        return [
            _make_export(web_module, name, fallback, allow_children)
            for name in export_names
        ]


def _make_export(
    web_module: WebModule, name: str, fallback: Optional[Any], allow_children: bool
) -> VdomDictConstructor:
    return partial(
        make_vdom_constructor(
            name,
            allow_children=allow_children,
        ),
        import_source=ImportSourceDict(
            source=web_module.source,
            sourceType=web_module.source_type,
            fallback=(fallback or web_module.default_fallback),
        ),
    )


def _web_module_path(name: str) -> Path:
    name += module_name_suffix(name)
    path = IDOM_WED_MODULES_DIR.current.joinpath(*name.split("/"))
    return path.with_suffix(path.suffix)
