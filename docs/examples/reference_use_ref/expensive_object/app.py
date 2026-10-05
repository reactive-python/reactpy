from reactpy import Ref, component, html, use_ref

# start


def build_word_index():
    """Stand-in for something slow: reading a file, opening a connection, etc."""
    return {word: len(word) for word in "react py is a python ui library".split()}


@component
def word_counter():
    # Built once, on the first render, and then reused for the life of the
    # component -- no `dependencies`, no invalidation, nothing to keep in sync.
    index: Ref[dict[str, int] | None] = use_ref(None)
    if index.current is None:
        index.current = build_word_index()

    return html.div(
        html.h1("Word lengths"),
        html.ul(
            [
                html.li(f"{word}: {length}")
                for word, length in sorted(index.current.items())
            ]
        ),
    )
