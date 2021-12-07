from idom import component, html, run, use_state


@component
def ColorButton():
    color, set_color = use_state("gray")

    def handle_click(event):
        set_color("orange")
        set_color("pink")
        set_color("blue")

    return html.button(
        {"onClick": handle_click, "style": {"backgroundColor": color}}, "Set Color"
    )


run(ColorButton)
