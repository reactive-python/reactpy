import mimetypes

# Fix for issue where Windows registry gets corrupt and mime types go missing
if not mimetypes.inited: # pragma: no cover
    mimetypes.init()
MIME_TYPES = {
    ".js": "application/javascript",
    ".css": "text/css",
    ".json": "application/json",
}
for extension, mime_type in MIME_TYPES.items():
    if not mimetypes.types_map.get(extension): # pragma: no cover
        mimetypes.add_type(mime_type, extension)
