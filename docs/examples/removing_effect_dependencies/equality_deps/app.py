"""React says a rebuilt object is a new dependency and will loop. In ReactPy
that is false: dependencies compare with `==`, so a rebuilt-but-equal dict
never re-triggers the Effect. Only real content changes do.

# start
"""

from reactpy import component, html, use_effect, use_state


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

    return html.div(
        html.button({"onClick": lambda e: set_page(page + 1)}, f"Page {page}"),
        html.ul([html.li({"key": row}, row) for row in rows]),
    )


# end


@component
def app():
    topic, set_topic = use_state("news")
    refreshes, set_refreshes = use_state(0)
    return html.div(
        html.button(
            {"onClick": lambda e: set_refreshes(refreshes + 1)},
            f"Re-render ({refreshes})",
        ),
        feed(topic),
    )
