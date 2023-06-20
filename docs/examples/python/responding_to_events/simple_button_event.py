from reactpy import component, html


@component
def button():
    def handle_click(event):
        print("You clicked me!")

    return html.button({"on_click": handle_click}, "Click me")



# end
if __name__ == "__main__":
    from reactpy import run
    from reactpy.utils import _read_docs_css

    @component
    def styled_app():
        return html._(html.style(_read_docs_css()), button())

    run(styled_app)
