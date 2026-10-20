"""Two runs of one async Effect can overlap; cancellation is not instant."""

import asyncio

from reactpy import component, html, use_async_effect, use_state


# start
@component
def poller(topic):
    async def effect():
        # A real request would go here. ReactPy cancels this task when `topic`
        # changes, but cancellation only takes effect at an await -- and code
        # that already ran cannot be un-run.
        print(f"start polling {topic}")
        try:
            await asyncio.sleep(0.4)
            print(f"finished polling {topic}")
        except asyncio.CancelledError:
            print(f"cancelled {topic}")
            raise

    use_async_effect(effect, dependencies=[topic])

    return html.p(f"polling {topic}")


@component
def app():
    topic, set_topic = use_state("news")

    async def handle_topic_click(event):
        set_topic("sports" if topic == "news" else "news")

    return html.div(
        html.button(
            {"onClick": handle_topic_click},
            "Switch topic",
        ),
        poller(topic),
    )
