from reactpy import component, html, use_ref


# start
@component
def counter():
    count = use_ref(0)

    def handle_click(event):
        # This doesn't re-render the component!
        count.current += 1

    return html.button({"onClick": handle_click}, f"You clicked {count.current} times")
