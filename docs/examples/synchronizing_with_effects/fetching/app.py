"""Fetch in an Effect; cancellation is what discards a stale answer."""

from data import catalog

from reactpy import component, html, use_async_effect, use_state


# start
@component
def report_view(name):
    rows, set_rows = use_state("nothing loaded yet")

    async def fetch():
        set_rows(f"loading {name} ...")
        result = await catalog.fetch(name)
        # This line is reached only if nobody cancelled the task. When `name`
        # changes, ReactPy cancels the running task before this line runs, so
        # an answer for the OLD report can never overwrite the new one.
        set_rows(result)

    use_async_effect(fetch, dependencies=[name])

    return html.div(html.h2(name), html.p(rows))


@component
def app():
    name, set_name = use_state("orders")

    async def handle_name_click(event):
        set_name("users" if name == "orders" else "orders")

    return html.div(
        html.button(
            {"onClick": handle_name_click},
            "Toggle report",
        ),
        report_view(name),
    )
