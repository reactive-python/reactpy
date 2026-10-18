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

    async def handle_draft_change(event):
        set_draft(await event.target.value)

    return html.div(
        html.h2(path),
        html.p(f"total reports sent: {len(analytics.sent)}"),
        html.input(
            {
                "placeholder": "notes",
                "onChange": handle_draft_change,
            }
        ),
    )


@component
def app():
    path, set_path = use_state("/home")

    async def handle_path_click(event):
        set_path("/about" if path == "/home" else "/home")

    return html.div(
        html.button(
            {"onClick": handle_path_click},
            "Navigate",
        ),
        page_view(path),
    )
