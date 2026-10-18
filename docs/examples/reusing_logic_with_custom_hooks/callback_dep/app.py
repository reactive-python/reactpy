"""Wrong: the custom Hook lists the callback it was given as its only
dependency. A local `def` compares code-equal across renders, so the Effect
never restarts and keeps reporting through the first render's closure.
"""

import asyncio

from reactpy import component, html, use_async_effect, use_ref, use_state


# start
def use_polling(on_result):
    async def loop():
        while True:
            await asyncio.sleep(0.2)
            on_result("poll finished")

    # `on_result` looks like a sensible dependency; it never counts as changed
    use_async_effect(loop, dependencies=[on_result])


@component
def dashboard():
    topic, set_topic = use_state("news")
    last, set_last = use_state("nothing yet")
    tick = use_ref(0)

    def on_result(value):
        tick.current += 1
        # reads `topic` from whichever render created this callback
        set_last(f"{value} #{tick.current} (handler saw topic={topic})")

    use_polling(on_result)

    async def handle_topic_click(e):
        set_topic(topic + "x")

    return html.div(
        html.button({"onClick": handle_topic_click}, f"Topic {topic}"),
        html.p(last),
    )


@component
def app():
    return dashboard()
