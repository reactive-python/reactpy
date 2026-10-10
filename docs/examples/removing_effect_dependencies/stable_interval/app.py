"""A user-adjustable delay must not restart the poll loop. Keep it in a ref
that is updated during render, and leave it out of the dependency list.
"""

import asyncio

from reactpy import component, html, use_async_effect, use_ref, use_state


# start
@component
def poller(topic):
    delay, set_delay = use_state(0.2)
    polls, set_polls = use_state(0)
    # updated during render, so the loop always sleeps with the newest value
    delay_ref = use_ref(delay)
    delay_ref.current = delay

    async def loop():
        print(f"start polling {topic}")
        try:
            while True:
                await asyncio.sleep(delay_ref.current)
                print(f"tick {topic} delay={delay_ref.current:.1f}s")
                # the loop is created once, so read state through an updater
                set_polls(lambda current: current + 1)
        except asyncio.CancelledError:
            print(f"stop polling {topic}")
            raise

    # `delay` is deliberately absent: adjusting it must not reconnect
    use_async_effect(loop, dependencies=[topic])

    return html.div(
        html.p(f"{topic}: {polls} polls"),
        html.button(
            {"onClick": lambda e: set_delay(delay + 0.2)}, f"Delay {delay:.1f}s"
        ),
    )


@component
def app():
    topic, set_topic = use_state("news")
    return html.div(
        html.button({"onClick": lambda e: set_topic(topic + "x")}, f"Topic {topic}"),
        poller(topic),
    )
