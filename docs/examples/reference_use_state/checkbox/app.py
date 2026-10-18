from reactpy import component, html, use_state


# start
@component
def checkbox():
    enabled, set_enabled = use_state(False)

    async def handle_change(event):
        # `checked` is read from the live element, like any other property.
        set_enabled(await event.target.checked)

    return html.div(
        html.label(
            html.input(
                {"type": "checkbox", "checked": enabled, "onChange": handle_change}
            ),
            "Enabled",
        ),
        html.p(f"Status: {'on' if enabled else 'off'}"),
    )
