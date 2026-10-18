"""React says a rebuilt object is a new dependency and will loop. In ReactPy
that is false: dependencies compare with `==`, so a rebuilt-but-equal dict
never re-triggers the Effect. Only real content changes do.
"""

from reactpy import component, html, use_effect, use_state


# start
@component
def feed(topic):
    page, set_page = use_state(1)
    rows, set_rows = use_state([])

    # rebuilt on every render, but compares equal to the previous one
    options = {"topic": topic, "per_page": 20}

    def load():
        print(f"loading {options} page={page}")
        set_rows([f"{topic} row {i} (page {page})" for i in range(3)])

    use_effect(load, dependencies=[options, page])

    async def handle_page_click(e):
        set_page(page + 1)

    return html.div(
        html.button({"onClick": handle_page_click}, f"Page {page}"),
        html.ul([html.li({"key": row}, row) for row in rows]),
    )


@component
def app():
    topic, set_topic = use_state("news")
    refreshes, set_refreshes = use_state(0)

    async def handle_refreshes_click(e):
        set_refreshes(refreshes + 1)

    return html.div(
        html.button(
            {"onClick": handle_refreshes_click},
            f"Re-render ({refreshes})",
        ),
        feed(topic),
    )
