from pathlib import Path
from typing import Any, Optional, Union

from idom import client
from idom.core.vdom import VdomDict, ImportSourceDict, make_vdom_constructor


class Module:
    """A Javascript module

    Parameters:
        name:
            If the module is installed, or ``source`` is not None, then this is the name
            the the module to import from (omit the ``.js`` file extension). Otherwise
            this is the URl (relative or absolute) to import from.
        source:
            Create a module of the given name using the given source code.
        replace:
            Overwrite a module defined from ``source`` if one of the same ``name``
            already exists, otherwise raise a ``ValueError`` complaining of name
            conflict.

    Returns:
        An :class:`Import` element for the newly defined module.
    """

    __slots__ = "_module", "_installed"

    def __init__(
        self,
        name: str,
        source: Optional[Union[str, Path]] = None,
        replace: bool = False,
    ) -> None:
        self._installed = False
        if source is not None:
            if replace:
                client.delete_web_modules([name], skip_missing=True)
            self._module = client.register_web_module(name, source)
            self._installed = True
        elif client.web_module_exists(name):
            self._module = client.web_module_url(name)
        else:
            self._module = name

    @property
    def installed(self) -> bool:
        return self._installed

    @property
    def url(self) -> str:
        return self._module

    def Import(self, name: str, *args: Any, **kwargs: Any) -> "Import":
        return Import(self._module, name, *args, **kwargs)

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
