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
from reactpy.asgi.executors.standalone import ReactPy, ReactPyApp
from reactpy.asgi.middleware import ReactPyMiddleware
from reactpy.asgi.utils import vdom_head_to_html
from reactpy.pyscript.utils import pyscript_component_html, pyscript_setup_html
from reactpy.types import (
    ReactPyConfig,
    VdomDict,
)


class ReactPyCSR(ReactPy):
    def __init__(
        self,
        *component_paths: str | Path,
        extra_py: tuple[str, ...] = (),
        extra_js: dict[str, Any] | str = "",
        pyscript_config: dict[str, Any] | str = "",
        root_name: str = "root",
        initial: str | VdomDict = "",
        http_headers: dict[str, str] | None = None,
        html_head: VdomDict | None = None,
        html_lang: str = "en",
        **settings: Unpack[ReactPyConfig],
    ) -> None:
        """Variant of ReactPy's standalone that only performs Client-Side Rendering (CSR).

        Parameters:
            ...
        """
        ReactPyMiddleware.__init__(
            self, app=ReactPyAppCSR(self), root_components=[], **settings
        )
        if not component_paths:
            raise ValueError("At least one component file path must be provided.")
        self.component_paths = tuple(str(path) for path in component_paths)
        self.extra_py = extra_py
        self.extra_js = extra_js
        self.pyscript_config = pyscript_config
        self.root_name = root_name
        self.initial = initial
        self.extra_headers = http_headers or {}
        self.dispatcher_pattern = re.compile(f"^{self.dispatcher_path}?")
        self.html_head = html_head or html.head()
        self.html_lang = html_lang

    def match_dispatch_path(self, scope: WebSocketScope) -> bool:
        return False


@dataclass
class ReactPyAppCSR(ReactPyApp):
    """ReactPy's standalone ASGI application for Client-Side Rendering (CSR)."""

    parent: ReactPyCSR
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
            file_paths=self.parent.component_paths,
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
