"""
Client Modules
==============
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union, overload
from urllib.parse import urlparse

from idom.config import IDOM_CLIENT_MODULES_MUST_HAVE_MOUNT
from idom.core.vdom import ImportSourceDict, VdomDict, make_vdom_constructor

from . import _private, manage


@overload
def install(
    packages: str,
    ignore_installed: bool,
    fallback: Optional[str],
) -> Module:
    ...


@overload
def install(
    packages: Union[List[str], Tuple[str]],
    ignore_installed: bool,
    fallback: Optional[str],
) -> List[Module]:
    ...


def install(
    packages: Union[str, List[str], Tuple[str]],
    ignore_installed: bool = False,
    fallback: Optional[str] = None,
    # dynamically installed modules probably won't have a mount so we default to False
    exports_mount: bool = False,
) -> Union[Module, List[Module]]:
    return_one = False
    if isinstance(packages, str):
        packages = [packages]
        return_one = True

    pkg_names = [_private.get_package_name(pkg) for pkg in packages]

    if ignore_installed or set(pkg_names).difference(manage.web_module_names()):
        manage.build(packages, clean_build=False)

    if return_one:
        return Module(pkg_names[0], fallback=fallback, exports_mount=exports_mount)
    else:
        return [
            Module(pkg, fallback=fallback, exports_mount=exports_mount)
            for pkg in pkg_names
        ]


NAME_SOURCE = "NAME"
"""A named souce - usually a Javascript package name"""

URL_SOURCE = "URL"
"""A source loaded from a URL, usually from a CDN"""

SOURCE_TYPES = {NAME_SOURCE, URL_SOURCE}
"""The possible source types for a :class:`Module`"""


class Module:
    """A Javascript module

    Parameters:
        source:
            The URL to an ECMAScript module which exports React components
            (*with* a ``.js`` file extension) or name of a module installed in the
            built-in client application (*without* a ``.js`` file extension).
        source_type:
            The type of the given ``source``. See :const:`SOURCE_TYPES` for the set of
            possible values.
        file:
            Only applicable if running on a client app which supports this feature.
            Dynamically install the code in the give file as a single-file module. The
            built-in client will inject this module adjacent to other installed modules
            which means they can be imported via a relative path like
            ``./some-other-installed-module.js``.
        fallack:
            What to display while the modules is being loaded.
        exports_mount:
            Whether the module exports a ``mount`` function that allows components to
            be mounted directly to the DOM. Such a mount function enables greater
            flexibility in how custom components can be implemented.

    Attributes:
        installed:
            Whether or not this module has been installed into the built-in client app.
        url:
            The URL this module will be imported from.
    """

    __slots__ = "source", "source_type", "fallback", "exports", "exports_mount"

    def __init__(
        self,
        source: str,
        source_type: Optional[str] = None,
        source_file: Optional[Union[str, Path]] = None,
        fallback: Optional[str] = None,
        exports_mount: bool = False,
        check_exports: Optional[bool] = None,
    ) -> None:
        self.source = source
        self.fallback = fallback
        self.exports_mount = exports_mount
        self.exports: Optional[Set[str]] = None

        if source_type is None:
            self.source_type = URL_SOURCE if _is_url(source) else NAME_SOURCE
        elif source_type in SOURCE_TYPES:
            self.source_type = source_type
        else:
            raise ValueError(f"Invalid source type {source_type!r}")

        if self.source_type == URL_SOURCE:
            if check_exports is True:
                raise ValueError(f"Can't check exports for source type {source_type!r}")
            elif source_file is not None:
                raise ValueError(f"File given, but source type is {source_type!r}")
            else:
                return None
        elif check_exports is None:
            check_exports = True

        if source_file is not None:
            manage.add_web_module(source, source_file)
        elif not manage.web_module_exists(source):
            raise ValueError(f"Module {source!r} does not exist")

        if check_exports:
            self.exports = manage.web_module_exports(source)
            if exports_mount and "mount" not in self.exports:
                raise ValueError(f"Module {source!r} does not export 'mount'")

    def declare(
        self,
        name: str,
        has_children: bool = True,
        fallback: Optional[str] = None,
    ) -> Import:
        """Return  an :class:`Import` for the given :class:`Module` and ``name``

        This roughly translates to the javascript statement

        .. code-block:: javascript

            import { name } from "module"

        Where ``name`` is the given name, and ``module`` is the :attr:`Module.url` of
        this :class:`Module` instance.
        """
        if self.exports is not None and name not in self.exports:
            raise ValueError(
                f"{self} does not export {name!r}, available options are {list(self.exports)}"
            )

        return Import(
            name,
            self.source,
            self.source_type,
            has_children,
            self.exports_mount,
            fallback or self.fallback,
        )

    def __getattr__(self, name: str) -> Import:
        if name[0].lower() == name[0]:
            # component names should be capitalized
            raise AttributeError(f"{self} has no attribute {name!r}")
        return self.declare(name)

    def __eq__(self, other: Any) -> bool:
        return (
            isinstance(other, Module)
            and self.source == other.source
            and self.source_type == other.source_type
        )

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.source})"


class Import:
    """Import a react module

    Once imported, you can instantiate the library's components by calling them
    via attribute-access.

    Examples:

        .. code-block:: python

            victory = idom.Import("victory", "VictoryBar" install=True)
            style = {"parent": {"width": "500px"}}
            victory.VictoryBar({"style": style}, fallback="loading...")
    """

    __slots__ = "_constructor", "_import_source", "_name"

    def __init__(
        self,
        name: str,
        source: str,
        source_type: str,
        has_children: bool = True,
        exports_mount: bool = False,
        fallback: Optional[str] = None,
    ) -> None:
        if IDOM_CLIENT_MODULES_MUST_HAVE_MOUNT.current and not exports_mount:
            # This check is not perfect since IDOM_CLIENT_MODULES_MUST_HAVE_MOUNT can be
            # set after Import instances have been constructed. A more comprehensive
            # check can be introduced if that is shown to be an issue in practice.
            raise RuntimeError(
                f"{IDOM_CLIENT_MODULES_MUST_HAVE_MOUNT} is set and {source} has no mount"
            )
        self._name = name
        self._constructor = make_vdom_constructor(name, has_children)
        self._import_source = ImportSourceDict(
            source=source,
            sourceType=source_type,
            fallback=fallback,
            exportsMount=exports_mount,
        )

    def __call__(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> VdomDict:
        return self._constructor(import_source=self._import_source, *args, **kwargs)

    def __repr__(self) -> str:
        info: Dict[str, Any] = {"name": self._name, **self._import_source}
        strings = ", ".join(f"{k}={v!r}" for k, v in info.items())
        return f"{type(self).__name__}({strings})"


def _is_url(string: str) -> bool:
    if string.startswith("/") or string.startswith("./") or string.startswith("../"):
        return True
    else:
        parsed = urlparse(string)
        return bool(parsed.scheme and parsed.netloc)
