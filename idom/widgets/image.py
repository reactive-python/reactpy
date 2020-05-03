from base64 import b64encode
from io import BytesIO

from typing import Any, Dict, Union, Optional

from idom.core.element import AbstractElement


class Image(AbstractElement):
    """An image element.

    Parameters:
        format: The format of the image source (e.g. png or svg)
        value: The image source. If not given use :attr:`Image.io` instead.
        attributes: Attributes assigned to the ``<image/>`` element.
    """

    __slots__ = ("_format", "_buffer", "_attributes", "_final_source")

    def __init__(
        self, format: str, value: str = "", attributes: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__()
        if format == "svg":
            format = "svg+xml"
        self._buffer = BytesBuffer(value)
        self._format = format
        self._attributes = attributes or {}

    @property
    def io(self) -> "BytesBuffer":
        """A file-like interface for write the image source."""
        return self._buffer

    @property
    def source(self) -> bytes:
        return self.io.getvalue().strip()

    @property
    def base64_source(self) -> str:
        return b64encode(self.source).decode()

    async def render(self) -> Dict[str, Any]:
        src = self.base64_source
        attrs = self._attributes.copy()
        attrs["src"] = f"data:image/{self._format};base64,{src}"
        return {"tagName": "img", "attributes": attrs}


class BytesBuffer(BytesIO):
    """Similar to :class:`BytesIO` but converts unicode to bytes automatically.

    Parameters:
        value: Initial value for the buffer.
        close_callback: Called with the value of the buffer when it is closed.
    """

    def __init__(self, value: Union[bytes, str]) -> None:
        if isinstance(value, str):
            super().__init__(value.encode())
        else:
            super().__init__(value)

    def write(self, value: Union[bytes, str]) -> int:
        if isinstance(value, str):
            return super().write(value.encode())
        else:
            return super().write(value)
