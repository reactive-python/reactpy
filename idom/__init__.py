from pkg_resources import (
    get_distribution as _get_distribution,
    DistributionNotFound as _DistributionNotFound,
)

try:
    __version__: str = _get_distribution(__name__).version
except _DistributionNotFound:  # pragma: no cover
    # package is not installed
    __version__ = "0.0.0"

from .utils import Ref, html_to_vdom

from .core.element import element, Element
from .core.events import event, Events
from .core.layout import Layout
from .core.vdom import vdom, VdomDict
from .core import hooks

from .widgets.html import html
from .widgets.utils import hotswap, multiview

from .client.module import Module, Import, install
from .client.protocol import client_implementation as client

from .server.prefab import run

from . import widgets

# try to automatically setup the dialect's import hook
try:
    import pyalect
    import tagged
    import htm
except ImportError:  # pragma: no cover
    pass
else:
    from . import dialect

    del pyalect
    del tagged
    del htm


__all__ = [
    "run",
    "element",
    "Element",
    "event",
    "Events",
    "dialect",
    "html",
    "hooks",
    "Layout",
    "server",
    "Ref",
    "vdom",
    "Module",
    "Import",
    "hotswap",
    "multiview",
    "JupyterDisplay",
    "html_to_vdom",
    "VdomDict",
    "widgets",
    "client",
    "install",
]
