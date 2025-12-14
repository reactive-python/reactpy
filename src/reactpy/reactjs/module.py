from __future__ import annotations

import logging
from pathlib import Path, PurePosixPath
from typing import Any, Literal

from reactpy import config
from reactpy.config import REACTPY_DEBUG, REACTPY_WEB_MODULES_DIR
from reactpy.core.vdom import Vdom
from reactpy.reactjs.types import NAME_SOURCE, URL_SOURCE
from reactpy.reactjs.utils import (
    are_files_identical,
    copy_file,
    file_lock,
    resolve_names_from_file,
    resolve_names_from_url,
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
        import_names=(
            resolve_names_from_url(url, resolve_imports_depth)
            if resolve_imports
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

    with file_lock(target_file.with_name(f"{target_file.name}.lock")):
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
            copy_file(target_file, source_file, symlink)

    return JavaScriptModule(
        source=name,
        source_type=NAME_SOURCE,
        default_fallback=fallback,
        file=target_file,
        import_names=(
            resolve_names_from_file(source_file, resolve_imports_depth)
            if resolve_imports
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
        import_names=(
            resolve_names_from_file(target_file, resolve_imports_depth)
            if resolve_imports
            else None
        ),
        unmount_before_update=unmount_before_update,
    )


def module_to_vdom(
    web_module: JavaScriptModule,
    import_names: str | list[str] | tuple[str, ...],
    fallback: Any | None = None,
    allow_children: bool = True,
) -> VdomConstructor | list[VdomConstructor]:
    """Return one or more VDOM constructors from a :class:`JavaScriptModule`

    Parameters:
        import_names:
            One or more names to import. If given as a string, a single component
            will be returned. If a list is given, then a list of components will be
            returned.
        fallback:
            What to temporarily display while the module is being loaded.
        allow_children:
            Whether or not these components can have children.
    """
    if isinstance(import_names, str):
        if (
            web_module.import_names is not None
            and import_names.split(".")[0] not in web_module.import_names
        ):
            msg = f"{web_module.source!r} does not contain {import_names!r}"
            raise ValueError(msg)
        return make_module(web_module, import_names, fallback, allow_children)
    else:
        if web_module.import_names is not None:
            missing = sorted(
                {e.split(".")[0] for e in import_names}.difference(
                    web_module.import_names
                )
            )
            if missing:
                msg = f"{web_module.source!r} does not contain {missing!r}"
                raise ValueError(msg)
        return [
            make_module(web_module, name, fallback, allow_children)
            for name in import_names
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


def import_reactjs(
    framework: Literal["preact", "react"] | None = None,
    version: str | None = None,
    use_local: bool = False,
):
    """
    Return an import map script tag for ReactJS or Preact.
    Parameters:
        framework:
            The framework to use, either "preact" or "react". Defaults to "preact" for
            performance reasons. Set this to `react` if you are experiencing compatibility
            issues with your component library.
        version:
            The version of the framework to use. Example values include "18", "10.2.4",
            or "latest". If left as `None`, a default version will be used depending on the
            selected framework.
        use_local:
            Whether to use the local framework ReactPy is bundled with (Preact).
    Raises:
        ValueError:
            If both `framework` and `react_url_prefix` are provided, or if
            `framework` is not one of "preact" or "react".
    Returns:
        A VDOM script tag containing the import map.
    """
    from reactpy import html

    if use_local and (framework or version):  # nocov
        raise ValueError("use_local cannot be used with framework or version")

    framework = framework or "preact"
    if framework and framework not in {"preact", "react"}:  # nocov
        raise ValueError("framework must be 'preact' or 'react'")

    # Import map for ReactPy's local framework (re-exported/bundled/minified version of Preact)
    if use_local:
        prefix = f"/{config.REACTPY_PATH_PREFIX.current.strip('/')}/static/{framework}"
        return html.script(
            {"type": "importmap"},
            f"""
            {{
                "imports": {{
                    "react": "{prefix}.js",
                    "react-dom": "{prefix}-dom.js",
                    "react-dom/client": "{prefix}-dom.js",
                    "react/jsx-runtime": "{prefix}-jsx-runtime.js"
                }}
            }}
            """,
        )

    # Import map for ReactJS from esm.sh
    if framework == "react":
        version = version or "19"
        postfix = "?dev" if REACTPY_DEBUG.current else ""
        return html.script(
            {"type": "importmap"},
            f"""
            {{
                "imports": {{
                    "react": "https://esm.sh/react@{version}{postfix}",
                    "react-dom": "https://esm.sh/react-dom@{version}{postfix}",
                    "react-dom/client": "https://esm.sh/react-dom@{version}/client{postfix}",
                    "react/jsx-runtime": "https://esm.sh/react@{version}/jsx-runtime{postfix}"
                }}
            }}
            """,
        )

    # Import map for Preact from esm.sh
    if framework == "preact":
        version = version or "10"
        postfix = "?dev" if REACTPY_DEBUG.current else ""
        return html.script(
            {"type": "importmap"},
            f"""
            {{
                "imports": {{
                    "react": "https://esm.sh/preact@{version}/compat{postfix}",
                    "react-dom": "https://esm.sh/preact@{version}/compat{postfix}",
                    "react-dom/client": "https://esm.sh/preact@{version}/compat/client{postfix}",
                    "react/jsx-runtime": "https://esm.sh/preact@{version}/compat/jsx-runtime{postfix}"
                }}
            }}
            """,
        )


def module_name_suffix(name: str) -> str:
    if name.startswith("@"):
        name = name[1:]
    head, _, tail = name.partition("@")  # handle version identifier
    _, _, tail = tail.partition("/")  # get section after version
    return PurePosixPath(tail or head).suffix or ".js"


def get_module_path(name: str) -> Path:
    directory = REACTPY_WEB_MODULES_DIR.current
    path = directory.joinpath(*name.split("/"))
    return path.with_suffix(path.suffix)
