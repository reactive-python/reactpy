from reactpy import component, html, use_ref


# start
@component
def counter():
    clicks = use_ref(0)

    async def handle_click(event):
        clicks.current += 1
        # Nothing on screen changes, but the server console proves the ref is
        # really incrementing between clicks.
        print(f"You clicked {clicks.current} times!")

    return html.button({"onClick": handle_click}, "Click me!")
