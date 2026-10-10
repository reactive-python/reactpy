"""use_callback keeps a handler's identity stable while its dependencies are
unchanged. A theme change reuses it; a count change does not.

# start
"""

from reactpy import component, html, use_callback, use_ref, use_state


@component
def toolbar():
    count, set_count = use_state(0)
    theme, set_theme = use_state("light")
    previous = use_ref(object())

    def stable_handler(event):
        set_count(count + 1)

    # inferred dependencies: `count` is the only free variable
    on_click = use_callback(stable_handler)

    reused = previous.current is on_click
    previous.current = on_click

    return html.div(
        html.button({"onClick": on_click}, f"Count {count}"),
        html.button(
            {"onClick": lambda e: set_theme("dark" if theme == "light" else "light")},
            f"Theme {theme}",
        ),
        html.p("handler reused on this render" if reused else "handler recreated"),
    )


# end


@component
def app():
    return toolbar()
