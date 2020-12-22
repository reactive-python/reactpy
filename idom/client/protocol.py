from pathlib import Path
from typing import cast, List, Union, Set

from typing_extensions import Protocol

from idom.utils import Ref

from . import manage


class ClientImplementation(Protocol):
    """A minimal set of functions required to use :class:`~idom.client.module.Module`"""

    def web_module_url(self, package_name: str) -> str:
        """Return the URL to import the module with the given name."""

    def web_module_exports(self, package_name: str) -> List[str]:
        """Return a list of names exported by a Javascript module."""

    def web_module_exists(self, package_name: str) -> bool:
        """Whether or not the given web module exists or is installed"""

    def web_module_names(self) -> Set[str]:
        """The set of available web modules (without file extension)"""

    def web_module_path(self, package_name: str) -> Path:
        """Return the path to a web module's source"""

    def add_web_module(self, package_name: str, source: Union[Path, str]) -> str:
        """Return the URL of a module added under the given ``name`` and contents of ``source``"""


client_implementation: Ref[ClientImplementation] = Ref(
    cast(ClientImplementation, manage)
)
"""The current client implementation used by :class:`~idom.client.module.Module`"""
