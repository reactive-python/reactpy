"""Each render gets its own Effect, closing over that render's values."""

from reactpy import component, html, use_effect, use_state


# start
@component
def audit_log(room, message):
    entries, set_entries = use_state([])

    def effect():
        # This closure sees the `message` from the render that CREATED this
        # Effect -- not the newest one. The dependency list says when to make
        # a new Effect; the values it reads are frozen from that render.
        set_entries(lambda previous: [*previous, f"{room} <- {message}"])

    use_effect(effect, dependencies=[room])

    return html.ul(
        [html.li({"key": index}, line) for index, line in enumerate(entries)]
    )


@component
def app():
    room, set_room = use_state("lobby")
    message, set_message = use_state("hello")

    return html.div(
        html.p(f"room={room} message={message!r}"),
        html.button({"onClick": lambda event: set_message(message + "!")}, "Type !"),
        html.button(
            {"onClick": lambda event: set_room("dev" if room == "lobby" else "lobby")},
            "Switch room",
        ),
        audit_log(room, message),
    )
