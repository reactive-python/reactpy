from reactpy import html
from reactpy.core.events import EventHandler


# start
# A plain callable gets the browser's argument list UNPACKED.
def plain_handler(event):
    print(event["target"]["value"])  # the event dict


# An EventHandler gets the LIST ITSELF.
async def list_handler(data):
    print(data[0]["target"]["value"])  # index first


html.button({"onClick": plain_handler}, "a")
html.button({"onClick": EventHandler(list_handler, prevent_default=True)}, "b")

# Converting one to the other without changing the body breaks it:
# TypeError: list indices must be integers or slices, not str
# end
