from reactpy import component, html, use_state


@component
def my_app():
    return html.div(
        html.h1("Counters that update separately"),
        my_button(),
        my_button(),
    )


@component
def my_button():
    count, set_count = use_state(0)

    def handle_click(event):
        set_count(count + 1)

    return html.button({"on_click": handle_click}, f"Clicked {count} times")


# end
if __name__ == "__main__":
    from reactpy import run
    from reactpy.utils import _read_docs_css

    @component
    def styled_app():
        return html._(html.style(_read_docs_css()), my_app())

    run(styled_app)
