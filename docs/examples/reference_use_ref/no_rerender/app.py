from reactpy import component, html, use_ref, use_state

# start


@component
def counter():
    # Two buttons, one counter each. Only the state one causes a render, so the
    # numbers only come back into sync on a render triggered by something else.
    state_count, set_state_count = use_state(0)
    ref_count = use_ref(0)

    async def bump_state(event=None):
        set_state_count(state_count + 1)

    async def bump_ref(event=None):
        ref_count.current += 1  # writes in place: no render is scheduled

    return html.div(
        html.p(f"state: {state_count}"),
        html.p(f"ref: {ref_count.current}"),
        html.button({"onClick": bump_state}, "Increment state"),
        html.button({"onClick": bump_ref}, "Increment ref"),
    )
