from idom import component, html, run, use_state


@component
def ColorButton():
    color, set_color = use_state("gray")

    def handle_click(event):
        set_color("orange")
        set_color("pink")
        set_color("blue")

    def handle_reset(event):
        set_color("gray")

    return html.div(
        html.button(
            "Set Color", on_click=handle_click, style={"background_color": color}
        ),
        html.button("Reset", on_click=handle_reset, style={"background_color": color}),
    )


run(ColorButton)
