"""Two synchronizations crammed into one Effect: changing the page tears the
connection down, and changing the topic re-fetches the page. Split them and
each owns its own dependencies and clean-up.
"""

from reactpy import component, html, use_effect, use_state


# start
@component
def feed(topic):
    page, set_page = use_state(1)
    rows, set_rows = use_state([])
    online, set_online = use_state(True)

    def subscribe():
        # one Effect doing two unrelated jobs: connect AND load rows
        if not online:
            print("offline — nothing to do")
            return
        print(f"connect {topic} page={page}")
        set_rows([f"{topic} row {i} (page {page})" for i in range(3)])

        def close():
            print(f"disconnect {topic} page={page}")

        return close

    use_effect(subscribe, dependencies=[topic, page, online])

    return html.div(
        html.button({"onClick": lambda e: set_page(page + 1)}, f"Page {page}"),
        html.button({"onClick": lambda e: set_online(not online)}, "Toggle online"),
        html.ul([html.li({"key": row}, row) for row in rows]),
    )


@component
def app():
    topic, set_topic = use_state("news")
    return html.div(
        html.button({"onClick": lambda e: set_topic(topic + "x")}, f"Topic {topic}"),
        feed(topic),
    )
