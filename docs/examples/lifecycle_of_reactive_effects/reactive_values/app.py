"""A value read by the Effect but missing from its dependencies goes stale."""

from data import log

from reactpy import component, html, use_effect, use_state


# start
@component
def counter():
    count, set_count = use_state(0)
    show_error, set_show_error = use_state(True)
    reports, set_reports = use_state([])

    def effect():
        # Reads `show_error`, but dependencies=[count] never mentions it. So
        # flipping show_error does not re-synchronize, and this keeps
        # reporting whatever show_error was when the Effect was created.
        line = f"count={count} reported_error={show_error}"
        log.append(line)
        set_reports(lambda previous: [*previous, line])

    use_effect(effect, dependencies=[count])

    async def handle_count_click(event):
        set_count(count + 1)

    async def handle_show_error_click(event):
        set_show_error(not show_error)

    return html.div(
        html.h1(count),
        html.button({"onClick": handle_count_click}, "Add 1"),
        html.button(
            {"onClick": handle_show_error_click},
            f"Toggle error (currently {show_error})",
        ),
        html.p("Effect reports:"),
        html.ul([html.li({"key": index}, line) for index, line in enumerate(reports)]),
    )
