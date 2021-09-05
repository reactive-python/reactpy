from . import config, html, log, web
from .core import hooks
from .core.component import Component, component
from .core.events import EventHandler, event
from .core.layout import Layout
from .core.vdom import vdom
from .server.prefab import run
from .utils import Ref, html_to_vdom
from .widgets import hotswap, multiview


__author__ = "idom-team"
__version__ = "0.33.2"  # DO NOT MODIFY

__all__ = [
    "component",
    "Component",
    "config",
    "event",
    "EventHandler",
    "hooks",
    "hotswap",
    "html_to_vdom",
    "html",
    "Layout",
    "log",
    "multiview",
    "Ref",
    "run",
    "vdom",
    "web",
]
