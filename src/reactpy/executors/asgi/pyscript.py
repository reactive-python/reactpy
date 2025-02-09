from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import formatdate
from pathlib import Path
from typing import Any

from asgiref.typing import WebSocketScope
from typing_extensions import Unpack

from reactpy import html
from reactpy.executors.asgi.middleware import ReactPyMiddleware
from reactpy.executors.asgi.standalone import ReactPy, ReactPyApp
from reactpy.executors.utils import vdom_head_to_html
from reactpy.pyscript.utils import pyscript_component_html, pyscript_setup_html
from reactpy.types import ReactPyConfig, VdomDict


class ReactPyPyscript(ReactPy):
    def __init__(
        self,
        *file_paths: str | Path,
        extra_py: tuple[str, ...] = (),
        extra_js: dict[str, str] | None = None,
        pyscript_config: dict[str, Any] | None = None,
        root_name: str = "root",
        initial: str | VdomDict = "",
        http_headers: dict[str, str] | None = None,
        html_head: VdomDict | None = None,
        html_lang: str = "en",
        **settings: Unpack[ReactPyConfig],
    ) -> None:
        """Variant of ReactPy's standalone that only performs Client-Side Rendering (CSR) via
        PyScript (using the Pyodide interpreter).

        This ASGI webserver is only used to serve the initial HTML document and static files.

        Parameters:
            file_paths:
                File path(s) to the Python files containing the root component. If multuple paths are
                provided, the components will be concatenated in the order they were provided.
            extra_py:
                Additional Python packages to be made available to the root component. These packages
                will be automatically installed from PyPi. Any packages names ending with `.whl` will
                be assumed to be a URL to a wheel file.
            extra_js: Dictionary where the `key` is the URL to the JavaScript file and the `value` is
                the name you'd like to export it as. Any JavaScript files declared here will be available
                to your root component via the `pyscript.js_modules.*` object.
            pyscript_config:
                Additional configuration options for the PyScript runtime. This will be merged with the
                default configuration.
            root_name: The name of the root component in your Python file.
            initial: The initial HTML that is rendered prior to your component loading in. This is most
                commonly used to render a loading animation.
            http_headers: Additional headers to include in the HTTP response for the base HTML document.
            html_head: Additional head elements to include in the HTML response.
            html_lang: The language of the HTML document.
            settings:
                Global ReactPy configuration settings that affect behavior and performance. Most settings
                are not applicable to CSR and will have no effect.
        """
        ReactPyMiddleware.__init__(
            self, app=ReactPyPyodideApp(self), root_components=[], **settings
        )
        if not file_paths:
            raise ValueError("At least one component file path must be provided.")
        self.file_paths = tuple(str(path) for path in file_paths)
        self.extra_py = extra_py
        self.extra_js = extra_js or {}
        self.pyscript_config = pyscript_config or {}
        self.root_name = root_name
        self.initial = initial
        self.extra_headers = http_headers or {}
        self.dispatcher_pattern = re.compile(f"^{self.dispatcher_path}?")
        self.html_head = html_head or html.head()
        self.html_lang = html_lang

    def match_dispatch_path(self, scope: WebSocketScope) -> bool:  # pragma: no cover
        """We do not use a WebSocket dispatcher for Client-Side Rendering (CSR)."""
        return False


@dataclass
class ReactPyPyodideApp(ReactPyApp):
    """ReactPy's standalone ASGI application for Client-Side Rendering (CSR)."""

    parent: ReactPyPyscript
    _index_html = ""
    _etag = ""
    _last_modified = ""

    def render_index_html(self) -> None:
        """Process the index.html and store the results in this class."""
        head_content = vdom_head_to_html(self.parent.html_head)
        pyscript_setup = pyscript_setup_html(
            extra_py=self.parent.extra_py,
            extra_js=self.parent.extra_js,
            config=self.parent.pyscript_config,
        )
        pyscript_component = pyscript_component_html(
            file_paths=self.parent.file_paths,
            initial=self.parent.initial,
            root=self.parent.root_name,
        )
        head_content = head_content.replace("</head>", f"{pyscript_setup}</head>")

        self._index_html = (
            "<!doctype html>"
            f'<html lang="{self.parent.html_lang}">'
            f"{head_content}"
            "<body>"
            f"{pyscript_component}"
            "</body>"
            "</html>"
        )
        self._etag = f'"{hashlib.md5(self._index_html.encode(), usedforsecurity=False).hexdigest()}"'
        self._last_modified = formatdate(
            datetime.now(tz=timezone.utc).timestamp(), usegmt=True
        )
