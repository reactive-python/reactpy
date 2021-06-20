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
"""A source loaded from a URL, usually a CDN"""


def module_from_url(
    url: str,
    fallback: Optional[Any] = None,
    resolve_exports: bool = IDOM_DEBUG_MODE.current,
    resolve_exports_depth: int = 5,
) -> WebModule:
    """Load a :class:`WebModule` from a :data:`URL_SOURCE`

    Parameters:
        url:
            Where the javascript module will be loaded from which conforms to the
            interface for :ref:`Custom Javascript Components`
        fallback:
            What to temporarilly display while the module is being loaded.
        resolve_imports:
            Whether to try and find all the named exports of this module.
        resolve_exports_depth:
            How deeply to search for those exports.
    """
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
    package: str,
    cdn: str = "https://esm.sh",
    fallback: Optional[Any] = None,
    resolve_exports: bool = IDOM_DEBUG_MODE.current,
    resolve_exports_depth: int = 5,
) -> WebModule:
    """Load a :class:`WebModule` from a :data:`URL_SOURCE` using a known framework

    Parameters:
        template:
            The name of the template to use with the given ``package`` (``react`` | ``preact``)
        package:
            The name of a package to load. May include a file extension (defaults to
            ``.js`` if not given)
        cdn:
            Where the package should be loaded from. The CDN must distribute ESM modules
        fallback:
            What to temporarilly display while the module is being loaded.
        resolve_imports:
            Whether to try and find all the named exports of this module.
        resolve_exports_depth:
            How deeply to search for those exports.
    """
    cdn = cdn.rstrip("/")

    template_file_name = f"{template}{module_name_suffix(package)}"
    template_file = Path(__file__).parent / "templates" / template_file_name
    if not template_file.exists():
        raise ValueError(f"No template for {template_file_name!r} exists")

    target_file = _web_module_path(package)
    if not target_file.exists():
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_text(
            template_file.read_text().replace("$PACKAGE", package).replace("$CDN", cdn)
        )

    return WebModule(
        source=package + module_name_suffix(package),
        source_type=NAME_SOURCE,
        default_fallback=fallback,
        file=target_file,
        export_names=(
            resolve_module_exports_from_url(f"{cdn}/{package}", resolve_exports_depth)
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
    """Load a :class:`WebModule` from a :data:`URL_SOURCE` using a known framework

    Parameters:
        template:
            The name of the template to use with the given ``package``
        package:
            The name of a package to load. May include a file extension (defaults to
            ``.js`` if not given)
        cdn:
            Where the package should be loaded from. The CDN must distribute ESM modules
        fallback:
            What to temporarilly display while the module is being loaded.
        resolve_imports:
            Whether to try and find all the named exports of this module.
        resolve_exports_depth:
            How deeply to search for those exports.
    """
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
    """Return one or more VDOM constructors from a :class:`WebModule`

    Parameters:
        export_names:
            One or more names to export. If given as a string, a single component
            will be returned. If a list is given, then a list of components will be
            returned.
        fallback:
            What to temporarilly display while the module is being loaded.
        allow_children:
            Whether or not these components can have children.
    """
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
