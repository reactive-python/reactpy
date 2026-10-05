from data import bus

from reactpy import component, html, use_callback, use_effect, use_state

# start


@component
def listener():
    renders, set_renders = use_state(0)
    heard, set_heard = use_state(0)

    # The registry lives outside ReactPy, so nothing deduplicates it for you.
    # A plain `def` here would be a brand new function object on every render,
    # and the registry would therefore collect another handler each time --
    # all of which receive every message. Pinning the identity keeps exactly
    # one handler, however often this component renders.
    handler = use_callback(
        lambda message: set_heard(lambda previous: previous + 1), dependencies=[]
    )

    def subscribe():
        bus.subscribe(handler)

    use_effect(subscribe, dependencies=None)

    return html.div(
        html.p(f"renders: {renders}"),
        html.p(f"handlers registered: {len(bus.handlers)}"),
        html.p(f"this component heard: {heard}"),
        html.button({"onClick": lambda event: set_renders(renders + 1)}, "Re-render"),
        html.button({"onClick": lambda event: bus.publish("ping")}, "Publish"),
    )
