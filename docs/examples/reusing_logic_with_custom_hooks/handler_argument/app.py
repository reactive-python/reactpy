"""A custom Hook that takes a callback and lists it as a dependency silently
freezes: a local `def` compares code-equal, so the Effect keeps the first
render's closure. Read the callback through a ref instead.
"""

import asyncio

from reactpy import component, html, use_async_effect, use_ref, use_state


# start
def use_polling(topic, on_result):
    latest = use_ref(on_result)
    # always the newest callback, without making it a dependency
    latest.current = on_result

    async def loop():
        while True:
            await asyncio.sleep(0.2)
            latest.current(f"result for {topic}")

    # deliberately excludes on_result: listing it would never help anyway
    use_async_effect(loop, dependencies=[topic])


@component
def dashboard():
    topic, set_topic = use_state("news")
    last, set_last = use_state("nothing yet")

    def on_result(value):
        # reads `topic` from the render that created it
        set_last(f"{value} (topic was {topic})")

    use_polling(topic, on_result)

    async def handle_topic_click(e):
        set_topic(topic + "x")

    return html.div(
        html.button({"onClick": handle_topic_click}, f"Topic {topic}"),
        html.p(last),
    )


@component
def app():
    return dashboard()
