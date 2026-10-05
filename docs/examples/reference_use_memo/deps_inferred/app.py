from reactpy import component, html, use_memo, use_state

# start

counts = []  # demo-only: lets you *see* how often `count` actually runs


@component
def word_count():
    text, set_text = use_state("reactpy is a python ui library")
    upper, set_upper = use_state(False)

    # No `dependencies` argument at all. ReactPy inspects the function's
    # closure and infers the free variables it reads -- here that is `text`,
    # but not `upper`, so toggling the case does not redo the count.
    def count():
        counts.append(1)
        return len(text.split())

    total = use_memo(count)

    return html.div(
        html.h1(f"{total} words"),
        html.p(text.upper() if upper else text),
        html.p(f"counted {len(counts)} time(s)"),
        html.button({"onClick": lambda event: set_upper(not upper)}, "Toggle case"),
        html.input(
            {
                "value": text,
                "onChange": lambda event: set_text(event["target"]["value"]),
            }
        ),
    )
