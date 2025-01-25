import hashlib
import os
from collections.abc import Coroutine, Sequence
from email.utils import formatdate
from logging import getLogger
from pathlib import Path
from typing import Any, Callable

from reactpy.backend.middleware import ReactPyMiddleware
from reactpy.core.types import ComponentType

_logger = getLogger(__name__)


class ReactPyStandalone(ReactPyMiddleware):
    cached_index_html: str = ""
    etag: str = ""
    last_modified: str = ""
    templates_dir = Path(__file__).parent.parent / "templates"
    index_html_path = templates_dir / "index.html"

    def __init__(
        self,
        root_component: ComponentType,
        *,
        path_prefix: str = "reactpy/",
        web_modules_dir: Path | None = None,
        http_headers: dict[str, str | int] | None = None,
    ) -> None:
        super().__init__(
            app=self.standalone_app,
            root_components=[],
            path_prefix=path_prefix,
            web_modules_dir=web_modules_dir,
        )
        self.root_component = root_component
        self.extra_headers = http_headers or {}

    async def standalone_app(
        self,
        scope: dict[str, Any],
        receive: Callable[..., Coroutine],
        send: Callable[..., Coroutine],
    ) -> None:
        """ASGI app for ReactPy standalone mode."""
        if scope["type"] != "http":
            if scope["type"] != "lifespan":
                _logger.warning(
                    "ReactPy app received unsupported request of type '%s' at path '%s'",
                    scope["type"],
                    scope["path"],
                )
            return

        # Store the HTTP response in memory for performance
        if not self.cached_index_html:
            await self.process_index_html()

        # Return headers for all HTTP responses
        request_headers = dict(scope["headers"])
        response_headers: dict[str, str | int] = {
            "etag": f'"{self.etag}"',
            "last-modified": self.last_modified,
            "access-control-allow-origin": "*",
            "cache-control": "max-age=60, public",
            **self.extra_headers,
        }

        # Browser is asking for the headers
        if scope["method"] == "HEAD":
            return await http_response(
                scope["method"],
                send,
                200,
                "",
                content_type=b"text/html",
                headers=self.dict_to_byte_list(response_headers),
            )

        # Browser already has the content cached
        if request_headers.get(b"if-none-match") == self.etag.encode():
            return await http_response(
                scope["method"],
                send,
                304,
                "",
                content_type=b"text/html",
                headers=self.dict_to_byte_list(response_headers),
            )

        # Send the index.html
        await http_response(
            scope["method"],
            send,
            200,
            self.cached_index_html,
            content_type=b"text/html",
            headers=self.dict_to_byte_list(
                response_headers | {"content-length": len(self.cached_index_html)}
            ),
        )

    def match_dispatch_path(self, scope: dict) -> bool:
        """Check if the path matches the dispatcher path."""
        return str(scope["path"]).startswith(self.dispatcher_path)

    async def process_index_html(self):
        """Process the index.html file."""
        with open(self.index_html_path, encoding="utf-8") as file_handle:
            cached_index_html = file_handle.read()

        self.cached_index_html = self.find_and_replace(
            cached_index_html,
            {
                'from "index.ts"': f'from "{self.static_path}index.js"',
                "{path_prefix}": self.path_prefix,
                "{reconnect_interval}": "750",
                "{reconnect_max_interval}": "60000",
                "{reconnect_max_retries}": "150",
                "{reconnect_backoff_multiplier}": "1.25",
            },
        )

        self.etag = hashlib.md5(
            self.cached_index_html.encode(), usedforsecurity=False
        ).hexdigest()

        last_modified = os.stat(self.index_html_path).st_mtime
        self.last_modified = formatdate(last_modified, usegmt=True)

    # @staticmethod
    # def find_js_filename(content: str) -> str:
    #     """Find the qualified filename of the index.js file."""
    #     substring = 'src="reactpy/static/index-'
    #     location = content.find(substring)
    #     if location == -1:
    #         raise ValueError(f"Could not find {substring} in content")
    #     start = content[location + len(substring) :]
    #     end = start.find('"')
    #     return f"index-{start[:end]}"

    @staticmethod
    def dict_to_byte_list(
        data: dict[str, str | int],
    ) -> list[tuple[bytes, bytes]]:
        """Convert a dictionary to a list of byte tuples."""
        result: list[tuple[bytes, bytes]] = []
        for key, value in data.items():
            new_key = key.encode()
            new_value = (
                value.encode() if isinstance(value, str) else str(value).encode()
            )
            result.append((new_key, new_value))
        return result

    @staticmethod
    def find_and_replace(content: str, replacements: dict[str, str]) -> str:
        """Find and replace content. Throw and error if the substring is not found."""
        for key, value in replacements.items():
            if key not in content:
                raise ValueError(f"Could not find {key} in content")
            content = content.replace(key, value)
        return content


async def http_response(
    method: str,
    send: Callable[..., Coroutine],
    code: int,
    message: str,
    content_type: bytes = b"text/plain",
    headers: Sequence = (),
) -> None:
    """Send a simple response."""
    # Head requests don't need body content
    if method == "HEAD":
        await send(
            {
                "type": "http.response.start",
                "status": code,
                "headers": [*headers],
            }
        )
        await send({"type": "http.response.body"})
    else:
        await send(
            {
                "type": "http.response.start",
                "status": code,
                "headers": [(b"content-type", content_type), *headers],
            }
        )
        await send({"type": "http.response.body", "body": message.encode()})
