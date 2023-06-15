import mimetypes
from logging import getLogger

_logger = getLogger(__name__)

# Fix for missing mime types due to OS corruption/misconfiguration
# Example: https://github.com/encode/starlette/issues/829
if not mimetypes.inited:
    mimetypes.init()
for extension, mime_type in {
    ".js": "application/javascript",
    ".css": "text/css",
    ".json": "application/json",
}.items():
    if not mimetypes.types_map.get(extension):  # pragma: no cover
        _logger.warning(
            "Mime type '%s = %s' is missing. Please research how to "
            "fix missing mime types on your operating system.",
            extension,
            mime_type,
        )
        mimetypes.add_type(mime_type, extension)
