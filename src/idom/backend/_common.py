from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Awaitable, Sequence, cast

from asgiref.typing import ASGIApplication
from uvicorn.config import Config as UvicornConfig
from uvicorn.server import Server as UvicornServer

from idom import __file__ as _idom_file_path
from idom import html
from idom.config import IDOM_WEB_MODULES_DIR
from idom.core.types import VdomDict
from idom.utils import vdom_to_html


PATH_PREFIX = PurePosixPath("/_idom")
MODULES_PATH = PATH_PREFIX / "modules"
ASSETS_PATH = PATH_PREFIX / "assets"
STREAM_PATH = PATH_PREFIX / "stream"

CLIENT_BUILD_DIR = Path(_idom_file_path).parent / "_client"


async def serve_development_asgi(
    app: ASGIApplication | Any,
    host: str,
    port: int,
    started: asyncio.Event | None,
) -> None:
    """Run a development server for starlette"""
    server = UvicornServer(
        UvicornConfig(
            app,
            host=host,
            port=port,
            loop="asyncio",
            reload=True,
        )
    )

    coros: list[Awaitable[Any]] = [server.serve()]

    if started:
        coros.append(_check_if_started(server, started))

    try:
        await asyncio.gather(*coros)
    finally:
        await asyncio.wait_for(server.shutdown(), timeout=3)


async def _check_if_started(server: UvicornServer, started: asyncio.Event) -> None:
    while not server.started:
        await asyncio.sleep(0.2)
    started.set()


def safe_client_build_dir_path(path: str) -> Path:
    """Prevent path traversal out of :data:`CLIENT_BUILD_DIR`"""
    return traversal_safe_path(
        CLIENT_BUILD_DIR,
        *("index.html" if path in ("", "/") else path).split("/"),
    )


def safe_web_modules_dir_path(path: str) -> Path:
    """Prevent path traversal out of :data:`idom.config.IDOM_WEB_MODULES_DIR`"""
    return traversal_safe_path(IDOM_WEB_MODULES_DIR.current, *path.split("/"))


def traversal_safe_path(root: str | Path, *unsafe: str | Path) -> Path:
    """Raise a ``ValueError`` if the ``unsafe`` path resolves outside the root dir."""
    root = os.path.abspath(root)

    # Resolve relative paths but not symlinks - symlinks should be ok since their
    # presence and where they point is under the control of the developer.
    path = os.path.abspath(os.path.join(root, *unsafe))

    if os.path.commonprefix([root, path]) != root:
        # If the common prefix is not root directory we resolved outside the root dir
        raise ValueError("Unsafe path")

    return Path(path)


def read_client_index_html(options: CommonOptions) -> str:
    return (
        (CLIENT_BUILD_DIR / "index.html")
        .read_text()
        .format(__head__=vdom_head_elements_to_html(options.head))
    )


def vdom_head_elements_to_html(head: Sequence[VdomDict] | VdomDict | str) -> str:
    if isinstance(head, str):
        return head
    elif isinstance(head, dict):
        if head.get("tagName") == "head":
            head = cast(VdomDict, {**head, "tagName": ""})
        return vdom_to_html(head)
    else:
        return vdom_to_html(html._(head))


@dataclass
class CommonOptions:
    """Options for IDOM's built-in backed server implementations"""

    head: Sequence[VdomDict] | VdomDict | str = (
        html.title("IDOM"),
        html.link(
            {
                "rel": "icon",
                "href": "_idom/assets/idom-logo-square-small.svg",
                "type": "image/svg+xml",
            }
        ),
    )
    """Add elements to the ``<head>`` of the application.

    For example, this can be used to customize the title of the page, link extra
    scripts, or load stylesheets.
    """

    url_prefix: str = ""
    """The URL prefix where IDOM resources will be served from"""
