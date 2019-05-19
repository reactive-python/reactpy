from base64 import b64encode
from io import BytesIO

from typing import Any, Dict, Union, Callable

from idom.core import AbstractElement


class Image(AbstractElement):
    """An image element.

    Parameters:
        format: The format of the image source (e.g. png or svg)
        value: The image source. If not given use :attr:`Image.io` instead.
        attributes: Attributes assigned to the ``<image/>`` element.
    """

    __slots__ = ("_source", "_format", "_buffer", "_attributes")

    def __init__(self, format: str, value: str = "", **attributes: Any) -> None:
        super().__init__()
        if format == "svg":
            format = "svg+xml"
        self._buffer = BytesBuffer(value.encode(), self._set_source)
        self._source = b""
        self._format = format
        self._attributes = attributes

    @property
    def io(self) -> "BytesBuffer":
        """A file-like interface for loading image source."""
        return self._buffer

    async def render(self) -> Dict[str, Any]:
        self._buffer.close()
        source = b64encode(self._source).decode()
        attrs = self._attributes.copy()
        attrs["src"] = f"data:image/{self._format};base64,{source}"
        return {"tagName": "img", "attributes": attrs}

    def _set_source(self, value: bytes) -> None:
        self._source = value


class BytesBuffer(BytesIO):
    """Similar to :class:`BytesIO` but converts unicode to bytes automatically.

    Parameters:
        value: Initial value for the buffer.
        close_callback: Called with the value of the buffer when it is closed.
    """

    def __init__(
        self, value: Union[bytes, str], close_callback: Callable[[bytes], None]
    ) -> None:
        self._on_close_callback = close_callback
        if isinstance(value, str):
            super().__init__(value.encode())
        else:
            super().__init__(value)

    def write(self, value: Union[bytes, str]) -> int:
        if isinstance(value, str):
            return super().write(value.encode())
        else:
            return super().write(value)

    def close(self) -> None:
        if not self.closed:
            self._on_close_callback(self.getvalue())
        super().close()
