from pathlib import Path
from typing import Any, Optional, Union
from urllib.parse import urlparse

from idom.core.vdom import VdomDict, ImportSourceDict, make_vdom_constructor

from .protocol import client_implementation as client


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

    Notes:
        To allow for other client implementations, you can set the current client
        implementation
        following private methods to support serving dynamically registered source
        files or loading modules that have been installed by some other means:
    """

    __slots__ = "url", "installed"

    def __init__(
        self,
        url_or_name: str,
        source_file: Optional[Union[str, Path]] = None,
    ) -> None:
        self.installed = False
        if source_file is not None:
            self.url = client.current.register_web_module(url_or_name, source_file)
            self.installed = True
        elif client.current.web_module_exists(url_or_name):
            self.url = client.current.web_module_url(url_or_name)
            self.installed = True
        elif _is_url(url_or_name):
            self.url = url_or_name
        else:
            raise ValueError(
                f"{url_or_name!r} is not installed - "
                "only installed modules can omit a file extension."
            )

    def Import(self, name: str, *args: Any, **kwargs: Any) -> "Import":
        """Return  an :class:`Import` for the given :class:`Module` and ``name``

        This roughly translates to the javascript statement

        .. code-block:: javascript

            import { name } from "module"

        Where ``name`` is the given name, and ``module`` is the :attr:`Module.url` of
        this :class:`Module` instance.
        """
        return Import(self.url, name, *args, **kwargs)

    def __repr__(self) -> str:  # pragma: no cover
        return f"{type(self).__name__}({self.url!r})"


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
        return bool(parsed.scheme and parsed.netloc)
