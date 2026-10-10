"""The setup/cleanup pair, and what a re-synchronization looks like."""

from data import server

from reactpy import component, html, use_effect, use_state


# start
@component
def room_view(room):
    def effect():
        # Setup: ReactPy runs this when the Effect is created.
        close = server.connect(room)

        # Clean-up: ReactPy runs this before the *next* run of this same
        # Effect, and again when the component unmounts. Together they make
        # one synchronization: connect this room, then leave it.
        def cleanup():
            close()

        return cleanup

    use_effect(effect, dependencies=[room])

    return html.p(f"{room} -- open connections: {server.open_count}")


@component
def app():
    room, set_room = use_state("lobby")

    return html.div(
        html.button(
            {"onClick": lambda event: set_room("dev" if room == "lobby" else "lobby")},
            f"Leave {room}",
        ),
        html.p("(server log is printed on the server console)"),
        room_view(room),
    )


# end
