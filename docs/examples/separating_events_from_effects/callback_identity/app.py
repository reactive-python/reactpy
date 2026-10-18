"""use_callback keeps a handler's identity stable while its dependencies are
unchanged. A theme change reuses it; a count change does not.
"""

from reactpy import component, html, use_callback, use_ref, use_state


# start
@component
def toolbar():
    count, set_count = use_state(0)
    theme, set_theme = use_state("light")
    previous = use_ref(object())

    async def stable_handler(event):
        set_count(count + 1)

    # inferred dependencies: `count` is the only free variable
    on_click = use_callback(stable_handler)

    reused = previous.current is on_click
    previous.current = on_click

    async def handle_theme_click(e):
        set_theme("dark" if theme == "light" else "light")

    return html.div(
        html.button({"onClick": on_click}, f"Count {count}"),
        html.button(
            {"onClick": handle_theme_click},
            f"Theme {theme}",
        ),
        html.p("handler reused on this render" if reused else "handler recreated"),
    )


@component
def app():
    return toolbar()
