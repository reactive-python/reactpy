from reactpy import component, html, use_memo, use_state

# start

# Module-level, so it is *not* a closure variable and ReactPy cannot infer it
# as a dependency.
config = {"prefix": "count"}

calls = []  # demo-only


@component
def counter():
    count, set_count = use_state(0)
    suffix, set_suffix = use_state("")

    def label():
        # Reads `config`, which ReactPy cannot see as a dependency. With
        # inferred (i.e. empty) dependencies this would be computed once and
        # then never notice an edited `config`. `dependencies=None` says: this
        # depends on the render itself, so recompute every time.
        calls.append(1)
        return f"{config['prefix']}: {count}{suffix}"

    async def handle_count_click(event):
        set_count(count + 1)

    async def handle_suffix_click(event):
        set_suffix("!")

    return html.div(
        html.h1(use_memo(label, dependencies=None)),
        html.p(f"label() ran {len(calls)} time(s)"),
        html.button({"onClick": handle_count_click}, "Count +1"),
        html.button({"onClick": handle_suffix_click}, "Set suffix"),
    )
