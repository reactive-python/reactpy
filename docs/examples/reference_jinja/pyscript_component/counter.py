from reactpy import component, html, use_state

# start


@component
def root():
    # `root` is the name the tag looks for by default; pass root="other" to
    # point it somewhere else. This file is inlined into the page at render
    # time and runs in the browser, so treat all of it as public.
    count, set_count = use_state(0)
    return html.div(
        html.h1(count),
        html.button({"onClick": lambda event: set_count(count + 1)}, "Add 1"),
    )
