from reactpy import component, html, use_effect, use_state


# start
@component
def logger():
    count, set_count = use_state(0)
    label, set_label = use_state("counter")
    runs, set_runs = use_state([])

    def effect():
        # No `dependencies` argument, so ReactPy infers them from the names
        # this closure reads. Only `count` is a real dependency here -- the
        # setter is stable, and `label` is not read at all. So pressing
        # Rename re-renders the component but does NOT re-run this effect.
        set_runs(lambda previous: [*previous, f"effect ran with count={count}"])

    use_effect(effect)

    return html.div(
        html.h1(count),
        html.button({"onClick": lambda event: set_count(count + 1)}, "Add 1"),
        html.button({"onClick": lambda event: set_label(label + "!")}, "Rename"),
        html.p(f"Label: {label}"),
        html.ul([html.li({"key": i}, line) for i, line in enumerate(runs)]),
    )
