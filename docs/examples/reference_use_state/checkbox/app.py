from reactpy import component, html, use_state


# start
@component
def checkbox():
    enabled, set_enabled = use_state(False)

    def handle_change(event):
        # `checked` is delivered by the client for checkbox inputs.
        set_enabled(event["target"]["checked"])

    return html.div(
        html.label(
            html.input(
                {"type": "checkbox", "checked": enabled, "onChange": handle_change}
            ),
            "Enabled",
        ),
        html.p(f"Status: {'on' if enabled else 'off'}"),
    )
