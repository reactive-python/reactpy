from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, overload

from reactpy.reactjs.module import (
    file_to_module,
    import_reactjs,
    module_to_vdom,
    string_to_module,
    url_to_module,
)
from reactpy.reactjs.types import (
    NAME_SOURCE,
    URL_SOURCE,
)
from reactpy.types import JavaScriptModule, VdomConstructor

__all__ = [
    "NAME_SOURCE",
    "URL_SOURCE",
    "component_from_file",
    "component_from_npm",
    "component_from_string",
    "component_from_url",
    "import_reactjs",
]

_URL_JS_MODULE_CACHE: dict[str, JavaScriptModule] = {}
_FILE_JS_MODULE_CACHE: dict[str, JavaScriptModule] = {}
_STRING_JS_MODULE_CACHE: dict[str, JavaScriptModule] = {}


@overload
def component_from_url(
    url: str,
    import_names: str,
    resolve_imports: bool = ...,
    resolve_imports_depth: int = ...,
    fallback: Any | None = ...,
    unmount_before_update: bool = ...,
    allow_children: bool = ...,
) -> VdomConstructor: ...


@overload
def component_from_url(
    url: str,
    import_names: list[str] | tuple[str, ...],
    resolve_imports: bool = ...,
    resolve_imports_depth: int = ...,
    fallback: Any | None = ...,
    unmount_before_update: bool = ...,
    allow_children: bool = ...,
) -> list[VdomConstructor]: ...


def component_from_url(
    url: str,
    import_names: str | list[str] | tuple[str, ...],
    resolve_imports: bool = False,
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
    if key in _URL_JS_MODULE_CACHE:
        module = _URL_JS_MODULE_CACHE[key]
    else:
        module = url_to_module(
            url,
            fallback=fallback,
            resolve_imports=resolve_imports,
            resolve_imports_depth=resolve_imports_depth,
            unmount_before_update=unmount_before_update,
        )
        _URL_JS_MODULE_CACHE[key] = module
    return module_to_vdom(module, import_names, fallback, allow_children)


@overload
def component_from_npm(
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
def component_from_npm(
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


def component_from_npm(
    package: str,
    import_names: str | list[str] | tuple[str, ...],
    resolve_imports: bool = False,
    resolve_imports_depth: int = 5,
    version: str = "latest",
    cdn: str = "https://esm.sh",
    fallback: Any | None = None,
    unmount_before_update: bool = False,
    allow_children: bool = True,
) -> VdomConstructor | list[VdomConstructor]:
    """Import a component from an NPM package.

    Is is mandatory to load `reactpy.reactjs.import_reactjs()` on your page before using this
    function. It is recommended to put this within your HTML <head> content.

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
            url += "&external=react,react-dom&bundle"
        else:
            url += "?external=react,react-dom&bundle"

    return component_from_url(
        url,
        import_names,
        fallback=fallback,
        resolve_imports=resolve_imports,
        resolve_imports_depth=resolve_imports_depth,
        unmount_before_update=unmount_before_update,
        allow_children=allow_children,
    )


@overload
def component_from_file(
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
def component_from_file(
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


def component_from_file(
    file: str | Path,
    import_names: str | list[str] | tuple[str, ...],
    resolve_imports: bool = False,
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
    if key in _FILE_JS_MODULE_CACHE:
        module = _FILE_JS_MODULE_CACHE[key]
    else:
        module = file_to_module(
            name,
            file,
            fallback=fallback,
            resolve_imports=resolve_imports,
            resolve_imports_depth=resolve_imports_depth,
            unmount_before_update=unmount_before_update,
            symlink=symlink,
        )
        _FILE_JS_MODULE_CACHE[key] = module
    return module_to_vdom(module, import_names, fallback, allow_children)


@overload
def component_from_string(
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
def component_from_string(
    content: str,
    import_names: list[str] | tuple[str, ...],
    resolve_imports: bool = ...,
    resolve_imports_depth: int = ...,
    name: str = "",
    fallback: Any | None = ...,
    unmount_before_update: bool = ...,
    allow_children: bool = ...,
) -> list[VdomConstructor]: ...


def component_from_string(
    content: str,
    import_names: str | list[str] | tuple[str, ...],
    resolve_imports: bool = False,
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
    if key in _STRING_JS_MODULE_CACHE:
        module = _STRING_JS_MODULE_CACHE[key]
    else:
        module = string_to_module(
            name,
            content,
            fallback=fallback,
            resolve_imports=resolve_imports,
            resolve_imports_depth=resolve_imports_depth,
            unmount_before_update=unmount_before_update,
        )
        _STRING_JS_MODULE_CACHE[key] = module
    return module_to_vdom(module, import_names, fallback, allow_children)
