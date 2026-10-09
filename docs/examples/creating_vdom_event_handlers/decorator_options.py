from reactpy import event, html


# start
# The @event decorator states the options outright.
@event(prevent_default=True, stop_propagation=True, debounce=250, throttle=100)
async def handle_key_down(event_data):
    print("key", event_data["key"])


html.input({"onKeyDown": handle_key_down})
# end
