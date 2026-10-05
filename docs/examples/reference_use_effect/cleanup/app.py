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

    return html.div(
        html.button(
            {"onClick": lambda event: set_connected(not connected)},
            "Connect" if not connected else "Disconnect",
        ),
        *([] if not connected else [connection()]),
    )
