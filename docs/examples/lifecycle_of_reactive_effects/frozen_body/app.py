"""A local function as a dependency never counts as changed."""

from data import log

from reactpy import component, html, use_effect, use_state


# start
@component
def counter():
    count, set_count = use_state(0)
    label, set_label = use_state("count")
    runs, set_runs = use_state([])

    def describe():
        # A fresh function object on every render -- but ReactPy compares two
        # such local functions by their *code*, not by identity
        # (core/hooks.py, strictly_equal). So `describe` never counts as
        # changed, and the Effect below keeps the closure it captured first.
        return f"{label}={count}"

    def effect():
        line = f"effect ran, describe() -> {describe()}"
        log.append(line)
        set_runs(lambda previous: [*previous, line])

    use_effect(effect, dependencies=[describe])

    return html.div(
        html.h1(f"{label}: {count}"),
        html.button({"onClick": lambda event: set_count(count + 1)}, "Add 1"),
        html.button({"onClick": lambda event: set_label(label + "!")}, "Rename"),
        html.p("Effect runs:"),
        html.ul([html.li({"key": index}, line) for index, line in enumerate(runs)]),
    )


# end
