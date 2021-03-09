from pkg_resources import DistributionNotFound as _DistributionNotFound
from pkg_resources import get_distribution as _get_distribution


try:
    __version__: str = _get_distribution(__name__).version
except _DistributionNotFound:  # pragma: no cover
    # package is not installed
    __version__ = "0.0.0"

from . import config, log
from .client.module import Import, Module, install
from .core import hooks
from .core.component import Component, component
from .core.events import Events, event
from .core.layout import Layout
from .core.vdom import VdomDict, vdom
from .server.prefab import run
from .utils import Ref, html_to_vdom
from .widgets.html import html
from .widgets.utils import hotswap, multiview


# try to automatically setup the dialect's import hook
try:
    import htm
    import pyalect
    import tagged
except ImportError:  # pragma: no cover
    pass
else:
    from . import dialect

    del pyalect
    del tagged
    del htm


__all__ = [
    "run",
    "component",
    "Component",
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
    "log",
    "config",
]
