"""Connect on mount, disconnect on unmount: the setup/cleanup pair."""

from data import chat_server

from reactpy import component, html, use_effect, use_state


# start
@component
def chat_room(room):
    status, set_status = use_state("offline")

    def effect():
        # ReactPy runs the returned function before the *next* run of this
        # same Effect, and again when the component unmounts. A connection
        # without a clean-up is a permanent leak in a long-lived server.
        close = chat_server.connect(room)
        set_status(f"connected to {room}")

        def cleanup():
            close()
            set_status("offline")

        return cleanup

    use_effect(effect, dependencies=[room])

    return html.p(status)


@component
def app():
    room, set_room = use_state("lobby")
    connected, set_connected = use_state(True)

    return html.div(
        html.button(
            {"onClick": lambda event: set_room("dev" if room == "lobby" else "lobby")},
            f"Switch room (now {room})",
        ),
        html.button(
            {"onClick": lambda event: set_connected(not connected)},
            "Leave" if connected else "Join",
        ),
        *([] if not connected else [chat_room(room)]),
    )
