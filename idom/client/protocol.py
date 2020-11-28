from typing import cast, List

from typing_extensions import Protocol

from idom.utils import Ref

from . import manage


class ClientImplementation(Protocol):
    """A minimal set of functions required to use :class:`idom.widget.module.Module`"""

    def web_module_url(self, source_name: str, package_name: str) -> str:
        """Return the URL to import the module with the given name."""

    def web_module_exports(self, source_name: str, package_name: str) -> List[str]:
        """Return a list of names exported by a Javascript module."""

    def web_module_exists(self, source_name: str, package_name: str) -> bool:
        """Whether or not the given web module exists or is installed"""


client_implementation: Ref[ClientImplementation] = Ref(
    cast(ClientImplementation, manage)
)
"""The current client implementation used by :class:`idom.widgets.module.Module`"""
