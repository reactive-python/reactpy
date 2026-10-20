from reactpy import component, html, use_state


# start
# A function that builds a fresh element on every call: the safe shape.
def status_banner(text, tone):
    return html.p(
        {"id": "status", "className": f"status-{tone}"},
        text,
    )


@component
def panel():
    n, set_n = use_state(0)
    tone = "ok" if n == 0 else "warn"

    async def handle_n_click(event):
        set_n(n + 1)

    return html.div(
        html.h1(f"n={n}"),
        html.button({"onClick": handle_n_click}, "bump"),
        status_banner(f"{n} items", tone),  # a new dict every render
    )


# end
