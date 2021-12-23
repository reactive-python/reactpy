from idom import component, html, run, use_state


@component
def CounterList():
    counters, set_counters = use_state([0, 0, 0])

    def make_increment_click_handler(index):
        def handle_click(event):
            new_value = counters[index] + 1
            set_counters(counters[:index] + [new_value] + counters[index + 1 :])

        return handle_click

    return html.ul(
        [
            html.li(
                count,
                html.button({"onClick": make_increment_click_handler(index)}, "+1"),
                key=index,
            )
            for index, count in enumerate(counters)
        ]
    )


run(CounterList)
