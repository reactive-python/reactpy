"""A locally defined function as a dependency never counts as changed, so the
callback is frozen on its first closure and stops seeing new values.
"""

from reactpy import component, html, use_callback, use_state


# start
@component
def search():
    query, set_query = use_state("")
    runs, set_runs = use_state(0)

    def describe():
        return f"query={query!r}"

    async def run(event):
        # `describe` is re-created every render but compares code-equal, so this
        # callback is still the one from the very first render. The functional
        # updater keeps the counter honest; only `describe()` is frozen.
        print(f"handler sees {describe()}")
        set_runs(lambda current: current + 1)

    on_click = use_callback(run, dependencies=[describe])

    async def handle_query_change(e):
        set_query(await e.target.value)

    return html.div(
        html.input({"value": query, "onChange": handle_query_change}),
        html.button({"onClick": on_click}, f"Run ({runs})"),
        html.p(f"page shows query={query!r} — compare with the console"),
    )


@component
def app():
    return search()
