from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union, overload
from urllib.parse import urlparse

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
) -> Union[Module, List[Module]]:
    return_one = False
    if isinstance(packages, str):
        packages = [packages]
        return_one = True

    pkg_names = [_private.get_package_name(pkg) for pkg in packages]

    if ignore_installed or set(pkg_names).difference(manage.web_module_names()):
        manage.build(packages, clean_build=False)

    if return_one:
        return Module(pkg_names[0], fallback=fallback)
    else:
        return [Module(pkg, fallback=fallback) for pkg in pkg_names]


class Module:
    """A Javascript module

    Parameters:
        url_or_name:
            The URL to an ECMAScript module which exports React components
            (*with* a ``.js`` file extension) or name of a module installed in the
            built-in client application (*without* a ``.js`` file extension).
        source_file:
            Only applicable if running on a client app which supports this feature.
            Dynamically install the code in the give file as a single-file module. The
            built-in client will inject this module adjacent to other installed modules
            which means they can be imported via a relative path like
            ``./some-other-installed-module.js``.

    Attributes:
        installed:
            Whether or not this module has been installed into the built-in client app.
        url:
            The URL this module will be imported from.
    """

    __slots__ = "url", "fallback", "exports", "_export_names"

    def __init__(
        self,
        url_or_name: str,
        source_file: Optional[Union[str, Path]] = None,
        fallback: Optional[str] = None,
        check_exports: bool = True,
    ) -> None:
        self.fallback = fallback
        self._export_names: Optional[List[str]] = None
        if source_file is not None:
            self.url = (
                manage.web_module_url(url_or_name)
                if manage.web_module_exists(url_or_name)
                else manage.add_web_module(url_or_name, source_file)
            )
            if check_exports:
                self._export_names = manage.web_module_exports(url_or_name)
        elif _is_url(url_or_name):
            self.url = url_or_name
        elif manage.web_module_exists(url_or_name):
            self.url = manage.web_module_url(url_or_name)
            if check_exports:
                self._export_names = manage.web_module_exports(url_or_name)
        else:
            raise ValueError(f"{url_or_name!r} is not installed or is not a URL")
        self.exports = {name: self.declare(name) for name in (self._export_names or [])}

    def declare(
        self,
        name: str,
        has_children: bool = True,
        fallback: Optional[str] = None,
    ) -> "Import":
        """Return  an :class:`Import` for the given :class:`Module` and ``name``

        This roughly translates to the javascript statement

        .. code-block:: javascript

            import { name } from "module"

        Where ``name`` is the given name, and ``module`` is the :attr:`Module.url` of
        this :class:`Module` instance.
        """
        if (
            self._export_names is not None
            # if 'default' is exported there's not much we can infer
            and "default" not in self._export_names
        ):
            if name not in self._export_names:
                raise ValueError(
                    f"{self} does not export {name!r}, available options are {self._export_names}"
                )
        return Import(self.url, name, has_children, fallback=fallback or self.fallback)

    def __getattr__(self, name: str) -> "Import":
        return self.exports.get(name) or self.declare(name)

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.url})"


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
        module: str,
        name: str,
        has_children: bool = True,
        fallback: Optional[str] = None,
    ) -> None:
        self._name = name
        self._constructor = make_vdom_constructor(name, has_children)
        self._import_source = ImportSourceDict(source=module, fallback=fallback)

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
