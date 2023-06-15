import mimetypes
from logging import getLogger

_logger = getLogger(__name__)

# Fix for missing mime types due to OS corruption/misconfiguration
if not mimetypes.inited:
    mimetypes.init()
MIME_TYPES = {
    ".js": "application/javascript",
    ".css": "text/css",
    ".json": "application/json",
}
for extension, mime_type in MIME_TYPES.items():
    if not mimetypes.types_map.get(extension):  # pragma: no cover
        _logger.warning(
            "Mime type '%s = %s' is missing. Please research how to "
            "fix missing mime types on your operating system.",
            extension,
            mime_type,
        )
        mimetypes.add_type(mime_type, extension)
