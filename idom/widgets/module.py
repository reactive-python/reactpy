from pathlib import Path
from typing import Any, Optional, Union
from urllib.parse import urlparse

from idom import client
from idom.core.vdom import VdomDict, ImportSourceDict, make_vdom_constructor


class Module:
    """A Javascript module

    Parameters:
        path:
            The URL to an ECMAScript module which exports React components
            (*with* a ``.js`` file extension) or name of a module installed in the
            built-in client application (*without* a ``.js`` file extension).
        source_file:
            Only applicable if running on the built-in client app. Dynamically install
            the code in the give file as a single-file module. The built-in client will
            inject this module adjacent to other installed modules which means they can
            be imported via a relative path (e.g. ``./some-other-installed-module.js``).

    .. warning::

        Do not use the ``source_file`` parameter if not running with the client app
        distributed with ``idom``.

    Examples:
        .. testcode::

            import idom

    """

    __slots__ = "_module", "_installed"

    def __init__(
        self,
        path: str,
        source_file: Optional[Union[str, Path]] = None,
    ) -> None:
        self._installed = False
        if source_file is not None:
            self._module = client.register_web_module(path, source_file)
            self._installed = True
        elif client.web_module_exists(path):
            self._module = client.web_module_url(path)
            self._installed = True
        elif not _is_url(path):
            raise ValueError(
                f"{path!r} is not installed - "
                "only installed modules can omit a file extension."
            )
        else:
            self._module = path

    @property
    def installed(self) -> bool:
        """Whether or not this module has been installed into the built-in client app."""
        return self._installed

    @property
    def url(self) -> str:
        """The path this module will be imported from"""
        return self._module

    def Import(self, name: str, *args: Any, **kwargs: Any) -> "Import":
        """Return  an :class:`Import` for the given :class:`Module` and ``name``

        This roughly translates to the javascript statement

        .. code-block:: javascript

            import { name } from "module"

        Where ``name`` is the given name, and ``module`` is the :attr:`Module.url` of
        this :class:`Module` instance.
        """
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


def _is_url(string: str) -> bool:
    if string.startswith("/") or string.startswith("./") or string.startswith("../"):
        return True
    else:
        parsed = urlparse(string)
        return parsed.scheme and parsed.netloc
