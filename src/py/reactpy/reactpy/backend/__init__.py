import mimetypes

# Fix for issue where Windows registry gets corrupt and mime types go missing
mimetypes.init()
MIME_TYPES = {
    ".js": "application/javascript",
    ".css": "text/css",
    ".ico": "image/x-icon",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".svg": "image/svg+xml",
    ".json": "application/json",
}
for extension, mime_type in MIME_TYPES.items():
    if not mimetypes.types_map.get(extension):
        mimetypes.add_type(mime_type, extension)
