from reactpy import html
from reactpy.core.events import EventHandler


# start
# A plain coroutine gets the browser's argument list UNPACKED.
async def plain_handler(event):
    print(await event.target.value)  # the event itself


# An EventHandler gets the LIST ITSELF: an EventArguments, a list subclass.
async def list_handler(data):
    print(await data[0].target.value)  # index first, then read as usual


html.button({"onClick": plain_handler}, "a")
html.button({"onClick": EventHandler(list_handler, prevent_default=True)}, "b")

# Hand the list to a body written for the event and the first read fails:
# AttributeError: 'EventArguments' object has no attribute 'target'
# Hand the event to a body written for the list and subscripting it fails:
# TypeError: 'Event' object is not subscriptable
# end
