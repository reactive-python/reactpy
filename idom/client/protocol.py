from typing import cast, Optional

from typing_extensions import Protocol

from idom.utils import Ref

from . import manage


class ClientImplementation(Protocol):
    """A minimal set of functions required to use :class:`idom.widget.module.Module`"""

    def web_module_url(self, source_name: str, package_name: str) -> Optional[str]:
        """Return the URL to import the module with the given name."""


client_implementation: Ref[ClientImplementation] = Ref(
    cast(ClientImplementation, manage)
)
"""The current client implementation used by :class:`idom.widgets.module.Module`"""
