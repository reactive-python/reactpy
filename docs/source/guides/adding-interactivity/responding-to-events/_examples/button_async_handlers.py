import asyncio

from idom import component, html, run


@component
def ButtonWithDelay(message, delay):
    async def handle_event(event):
        await asyncio.sleep(delay)
        print(message)

    return html.button(message, on_click=handle_event)


@component
def App():
    return html.div(
        ButtonWithDelay("print 3 seconds later", delay=3),
        ButtonWithDelay("print immediately", delay=0),
    )


run(App)
