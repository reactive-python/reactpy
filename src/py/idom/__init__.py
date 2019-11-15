__version__ = "0.6.0-a.4"

from . import server

from .core.element import element, Element
from .core.events import event, Events
from .core.layout import Layout
from .core.vdom import vdom

from .widgets.html import html
from .widgets.common import hotswap, Eval, Import
from .widgets.display import display
from .widgets.inputs import Input
from .widgets.images import Image

from .tools import Var, html_to_vdom

try:
    import pyalect
    import tagged
    import htm
except ImportError:
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
    "Eval",
    "Import",
    "hotswap",
    "display",
    "Input",
    "html_to_vdom",
]
