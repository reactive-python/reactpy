from reactpy import component, html, use_effect, use_state


@component
def connection():
    status, set_status = use_state("offline")

    def effect():
        # Returning a function registers it as clean-up. ReactPy runs it
        # before the next effect for this component, and again on unmount.
        set_status("online")
        print("connected")

        def cleanup():
            print("disconnected")

        return cleanup

    use_effect(effect, dependencies=[])

    return html.p(status)


# start
@component
def app():
    connected, set_connected = use_state(False)

    async def handle_connected_click(event):
        set_connected(not connected)

    return html.div(
        html.button(
            {"onClick": handle_connected_click},
            "Connect" if not connected else "Disconnect",
        ),
        *([] if not connected else [connection()]),
    )
