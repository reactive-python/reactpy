from pathlib import Path
from typing import Any, Optional, Union

from idom import client
from idom.core.vdom import VdomDict, ImportSourceDict, make_vdom_constructor


class Module:
    """A Javascript module

    Parameters:
        name:
            The module's name. If ``install`` or ``source`` are provided omit the ``.js``
            file extension. Otherwise this is the exact import path and could be anything
            including a URL.
        install:
            If a string, then the dependency string used to install a module with
            the given ``name`` (e.g. ``my-module@1.2.3``). If ``True`` then the given
            ``name`` will be used as the dependency string.
        source:
            Create a module of the given name using the given source code.

    Returns:
        An :class:`Import` element for the newly defined module.
    """

    __slots__ = ("_module", "_name", "_installed")

    def __init__(
        self,
        name: str,
        install: Union[bool, str] = False,
        source: Optional[Union[str, Path]] = None,
        replace: bool = False,
    ) -> None:
        self._installed = False
        if install and source:
            raise ValueError("Both 'install' and 'source' were given.")
        elif (install or source) and not replace and client.web_module_exists(name):
            self._module = client.web_module_url(name)
            self._installed = True
            self._name = name
        elif source is not None:
            self._module = client.register_web_module(name, source)
            self._installed = True
            self._name = name
        elif isinstance(install, str):
            client.install([install], [name])
            self._module = client.web_module_url(name)
            self._installed = True
            self._name = name
        elif install is True:
            client.install(name)
            self._module = client.web_module_url(name)
            self._installed = True
            self._name = name
        elif client.web_module_exists(name):
            self._module = client.web_module_url(name)
        else:
            self._module = name

    @property
    def name(self) -> str:
        if not self._installed:
            raise ValueError("Module is not installed locally")
        return self._name

    @property
    def url(self) -> str:
        return self._module

    def Import(self, name: str, *args: Any, **kwargs: Any) -> "Import":
        return Import(self._module, name, *args, **kwargs)

    def delete(self) -> None:
        if not self._installed:
            raise ValueError("Module is not installed locally")
        client.delete_web_modules([self._name])

    def __repr__(self) -> str:  # pragma: no cover
        return f"{type(self).__name__}({self._module!r})"


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

    __slots__ = ("_constructor", "_import_source")

    def __init__(
        self,
        module: str,
        name: str,
        has_children: bool = True,
        fallback: Optional[str] = "",
    ) -> None:
        self._constructor = make_vdom_constructor(name, has_children)
        self._import_source = ImportSourceDict(source=module, fallback=fallback)

    def __call__(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> VdomDict:
        return self._constructor(import_source=self._import_source, *args, **kwargs)

    def __repr__(self) -> str:  # pragma: no cover
        items = ", ".join(f"{k}={v!r}" for k, v in self._import_source.items())
        return f"{type(self).__name__}({items})"
