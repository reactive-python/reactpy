from reactpy import event, html


# start
# A bound method is a fine handler -- it fires. What is lost is detection of
# the event.preventDefault() inside it: the bytecode inspector reads the
# *first* parameter as the event, and for a method that is `self`.
class SearchForm:
    async def on_submit(self, event):
        event.preventDefault()


plain = html.form({"onSubmit": SearchForm().on_submit})["eventHandlers"]["onSubmit"]
print(plain.prevent_default)  # False -- your call was never seen


# Say it explicitly with @event and it works.
@event(prevent_default=True)
async def submit(event_data):
    print("submitted")


explicit = html.form({"onSubmit": submit})["eventHandlers"]["onSubmit"]
print(explicit.prevent_default)  # True
# end
