from pkg_resources import DistributionNotFound as _DistributionNotFound
from pkg_resources import get_distribution as _get_distribution


try:
    __version__: str = _get_distribution(__name__).version
except _DistributionNotFound:  # pragma: no cover
    # package is not installed
    __version__ = "0.0.0"

__author__ = "idom-team"

from . import config, html, log, web
from .core import hooks
from .core.component import Component, component
from .core.events import Events, event
from .core.layout import Layout
from .core.vdom import VdomDict, vdom
from .server.prefab import run
from .utils import Ref, html_to_vdom
from .widgets import hotswap, multiview


__all__ = [
    "config",
    "html",
    "log",
    "web",
    "hooks",
    "Component",
    "component",
    "Events",
    "event",
    "Layout",
    "VdomDict",
    "vdom",
    "run",
    "Ref",
    "html_to_vdom",
    "hotswap",
    "multiview",
]
