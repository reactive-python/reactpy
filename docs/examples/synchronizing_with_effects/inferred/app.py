"""An Effect with no dependencies argument infers them from the closure."""

from reactpy import component, html, use_effect, use_state


# start
@component
def counter():
    count, set_count = use_state(0)
    label, set_label = use_state("clicks")
    runs, set_runs = use_state([])

    def effect():
        # This closure reads `count` and nothing else, so `count` is the
        # Effect's only dependency. It never reads `label`, so renaming
        # re-renders the component WITHOUT re-running this Effect.
        set_runs(lambda previous: [*previous, f"effect ran with count={count}"])

    use_effect(effect)

    async def handle_count_click(event):
        set_count(count + 1)

    async def handle_label_click(event):
        set_label(label + "!")

    return html.div(
        html.h1(f"{label}: {count}"),
        html.button({"onClick": handle_count_click}, "Add 1"),
        html.button({"onClick": handle_label_click}, "Rename"),
        html.ul([html.li({"key": index}, line) for index, line in enumerate(runs)]),
    )
