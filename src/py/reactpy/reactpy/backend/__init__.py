import mimetypes

# Fix for issue where Windows registry gets corrupt and mime types go missing
mimetypes.init()
for extension, type in mimetypes.common_types.items():
    if not mimetypes.types_map.get(extension):
        mimetypes.add_type(type, extension)
