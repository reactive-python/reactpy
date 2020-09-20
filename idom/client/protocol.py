from pathlib import Path
from typing import Union, cast

from typing_extensions import Protocol

from idom import Ref

from . import manage


class ClientImplementation(Protocol):
    """A minimal set of functions required to use :class:`idom.widget.module.Module`"""

    def register_web_module(self, name: str, source: Union[str, Path]) -> str:
        """Return the URL of a module added under the given ``name`` and contents of ``source``"""

    def web_module_url(self, name: str) -> str:
        """Return the URL to import the module with the given name."""

    def web_module_exists(self, name: str) -> bool:
        """Check if a module with the given name is installed"""


client_implementation: Ref[ClientImplementation] = Ref(
    cast(ClientImplementation, manage)
)
"""The current client implementation used by :class:`idom.widgets.module.Module`"""
