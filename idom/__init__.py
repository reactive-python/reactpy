from pkg_resources import (
    get_distribution as _get_distribution,
    DistributionNotFound as _DistributionNotFound,
)

from .core.element import element, Element
from .core.events import event, Events
from .core.layout import Layout
from .core.vdom import vdom, VdomDict
from .core import hooks

from .widgets.html import html
from .widgets.utils import Module, Import, hotswap, multiview
from .widgets.jupyter import JupyterDisplay

from .utils import Ref, html_to_vdom

from . import server
from . import widgets

try:
    __version__ = _get_distribution(__name__).version
except _DistributionNotFound:  # pragma: no cover
    # package is not installed
    __version__ = "0.0.0"

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
]
