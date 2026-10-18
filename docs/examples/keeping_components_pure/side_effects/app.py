from reactpy import component, html, use_state


# start
@component
def tea_counter():
    sips, set_sips = use_state(0)

    async def take_a_sip(event):
        # Side effects belong here: this runs on click, not during rendering.
        set_sips(sips + 1)

    return html.div(
        html.h1(f"You have taken {sips} sips."),
        html.button({"onClick": take_a_sip}, "Take a sip"),
    )
