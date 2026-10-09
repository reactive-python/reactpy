"""Report a page view once per page, not once per render."""

from data import analytics

from reactpy import component, html, use_effect, use_state


# start
@component
def page_view(path):
    draft, set_draft = use_state("")

    def effect():
        # Depends on `path` only: editing the field re-renders the component
        # but does not report another visit.
        analytics.log_visit(path)

    use_effect(effect, dependencies=[path])

    return html.div(
        html.h2(path),
        html.p(f"total reports sent: {len(analytics.sent)}"),
        html.input(
            {
                "placeholder": "notes",
                "onChange": lambda event: set_draft(event["target"]["value"]),
            }
        ),
    )


@component
def app():
    path, set_path = use_state("/home")

    return html.div(
        html.button(
            {
                "onClick": lambda event: set_path(
                    "/about" if path == "/home" else "/home"
                )
            },
            "Navigate",
        ),
        page_view(path),
    )


# end
