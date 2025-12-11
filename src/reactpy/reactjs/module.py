from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from reactpy import config
from reactpy.config import REACTPY_WEB_MODULES_DIR
from reactpy.core.vdom import Vdom
from reactpy.reactjs.types import NAME_SOURCE, URL_SOURCE
from reactpy.reactjs.utils import (
    are_files_identical,
    copy_file,
    module_name_suffix,
    resolve_module_exports_from_file,
    resolve_module_exports_from_url,
)
from reactpy.types import ImportSourceDict, JavaScriptModule, VdomConstructor

logger = logging.getLogger(__name__)


def url_to_module(
    url: str,
    fallback: Any | None = None,
    resolve_imports: bool = True,
    resolve_imports_depth: int = 5,
    unmount_before_update: bool = False,
) -> JavaScriptModule:
    return JavaScriptModule(
        source=url,
        source_type=URL_SOURCE,
        default_fallback=fallback,
        file=None,
        export_names=(
            resolve_module_exports_from_url(url, resolve_imports_depth)
            if (
                resolve_imports
                if resolve_imports is not None
                else config.REACTPY_DEBUG.current
            )
            else None
        ),
        unmount_before_update=unmount_before_update,
    )


def file_to_module(
    name: str,
    file: str | Path,
    fallback: Any | None = None,
    resolve_imports: bool = True,
    resolve_imports_depth: int = 5,
    unmount_before_update: bool = False,
    symlink: bool = False,
) -> JavaScriptModule:
    name += module_name_suffix(name)

    source_file = Path(file).resolve()
    target_file = get_module_path(name)
    if not source_file.exists():
        msg = f"Source file does not exist: {source_file}"
        raise FileNotFoundError(msg)

    if not target_file.exists():
        copy_file(target_file, source_file, symlink)
    elif not are_files_identical(source_file, target_file):
        logger.info(
            f"Existing web module {name!r} will "
            f"be replaced with {target_file.resolve()}"
        )
        target_file.unlink()
        copy_file(target_file, source_file, symlink)

    return JavaScriptModule(
        source=name,
        source_type=NAME_SOURCE,
        default_fallback=fallback,
        file=target_file,
        export_names=(
            resolve_module_exports_from_file(source_file, resolve_imports_depth)
            if (
                resolve_imports
                if resolve_imports is not None
                else config.REACTPY_DEBUG.current
            )
            else None
        ),
        unmount_before_update=unmount_before_update,
    )


def string_to_module(
    name: str,
    content: str,
    fallback: Any | None = None,
    resolve_imports: bool = True,
    resolve_imports_depth: int = 5,
    unmount_before_update: bool = False,
) -> JavaScriptModule:
    name += module_name_suffix(name)

    target_file = get_module_path(name)

    if target_file.exists() and target_file.read_text(encoding="utf-8") != content:
        logger.info(
            f"Existing web module {name!r} will "
            f"be replaced with {target_file.resolve()}"
        )
        target_file.unlink()

    target_file.parent.mkdir(parents=True, exist_ok=True)
    target_file.write_text(content)

    return JavaScriptModule(
        source=name,
        source_type=NAME_SOURCE,
        default_fallback=fallback,
        file=target_file,
        export_names=(
            resolve_module_exports_from_file(target_file, resolve_imports_depth)
            if (
                resolve_imports
                if resolve_imports is not None
                else config.REACTPY_DEBUG.current
            )
            else None
        ),
        unmount_before_update=unmount_before_update,
    )


def module_to_vdom(
    web_module: JavaScriptModule,
    export_names: str | list[str] | tuple[str, ...],
    fallback: Any | None = None,
    allow_children: bool = True,
) -> VdomConstructor | list[VdomConstructor]:
    """Return one or more VDOM constructors from a :class:`JavaScriptModule`

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
        return make_module(web_module, export_names, fallback, allow_children)
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
            make_module(web_module, name, fallback, allow_children)
            for name in export_names
        ]


def make_module(
    web_module: JavaScriptModule,
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


def get_module_path(name: str) -> Path:
    directory = REACTPY_WEB_MODULES_DIR.current
    path = directory.joinpath(*name.split("/"))
    return path.with_suffix(path.suffix)


def import_reactjs():
    from reactpy import config, html

    base_url = config.REACTPY_PATH_PREFIX.current.strip("/")
    return html.script(
        {"type": "importmap"},
        f"""
        {{
            "imports": {{
                "react": "/{base_url}/static/react.js",
                "react-dom": "/{base_url}/static/react-dom.js",
                "react/jsx-runtime": "/{base_url}/static/react-jsx-runtime.js"
            }}
        }}
        """,
    )
