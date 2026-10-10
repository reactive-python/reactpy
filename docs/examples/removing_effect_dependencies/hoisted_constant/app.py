"""Values that cannot change across renders are not dependencies: hoist the
constant and the imported helper out of the component.

# start
"""

from reactpy import component, html, use_effect, use_state

PAGE_SIZE = 20
HEADERS = {"Accept": "application/json"}


def format_rows(topic, raw):
    """Module-level helper: same object on every render and every connection."""
    return [f"{topic}: {name}" for name in raw]


@component
def directory(topic):
    query, set_query = use_state("")
    rows, set_rows = use_state([])

    def load():
        raw = [f"user-{i}" for i in range(PAGE_SIZE // 4)]
        print(f"load topic={topic} page_size={PAGE_SIZE} headers={HEADERS}")
        set_rows(format_rows(topic, raw))

    # neither PAGE_SIZE, HEADERS, nor format_rows belongs in this list
    use_effect(load, dependencies=[topic])

    return html.div(
        html.input(
            {
                "value": query,
                "onChange": lambda e: set_query(e["target"]["value"]),
            }
        ),
        html.p(f"query={query!r} rows={len(rows)}"),
        html.ul([html.li({"key": row}, row) for row in rows]),
    )


# end


@component
def app():
    topic, set_topic = use_state("news")
    return html.div(
        html.button({"onClick": lambda e: set_topic(topic + "x")}, f"Topic {topic}"),
        directory(topic),
    )
