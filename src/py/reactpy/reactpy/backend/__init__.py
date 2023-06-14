import mimetypes
from logging import getLogger

_logger = getLogger(__name__)

# Fix for missing mime types due to corrupt Windows registry 
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
            f"Mime type '{mime_type}:{extension}' is missing."
            " Please determine how to fix missing mime types on your OS."
        )
        mimetypes.add_type(mime_type, extension)
