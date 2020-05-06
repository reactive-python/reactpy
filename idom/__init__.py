__version__ = "0.7.0-dev.1"

from . import server

from .core.element import element, Element
from .core.events import event, Events
from .core.layout import Layout
from .core.vdom import vdom

from .widgets.input import Input
from .widgets.html import html
from .widgets.utils import Module, Import, hotswap, multiview
from .widgets.display import display
from .widgets.image import Image

from .tools import Var, html_to_vdom

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
    "Layout",
    "server",
    "Var",
    "vdom",
    "Image",
    "Module",
    "Import",
    "hotswap",
    "multiview",
    "display",
    "Input",
    "html_to_vdom",
]
