from . import config, html, log, web
from .core import hooks
from .core.component import Component, component
from .core.dispatcher import Stop
from .core.events import EventHandler, event
from .core.hooks import (
    use_callback,
    use_effect,
    use_memo,
    use_reducer,
    use_ref,
    use_state,
)
from .core.layout import Layout
from .core.proto import ComponentType, VdomDict
from .core.vdom import vdom
from .sample import run_sample_app
from .server.prefab import run
from .utils import Ref, html_to_vdom
from .widgets import hotswap, multiview


__author__ = "idom-team"
__version__ = "0.35.0"  # DO NOT MODIFY

__all__ = [
    "component",
    "Component",
    "ComponentType",
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
    "run_sample_app",
    "run",
    "Stop",
    "use_callback",
    "use_effect",
    "use_memo",
    "use_reducer",
    "use_ref",
    "use_state",
    "vdom",
    "VdomDict",
    "web",
]
