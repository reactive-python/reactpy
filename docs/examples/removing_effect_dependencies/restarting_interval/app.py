"""The delay is in the dependency list, so every adjustment tears the poll loop
down and starts a new one — measured, four restarts where two were needed.
"""

import asyncio

from reactpy import component, html, use_async_effect, use_state


# start
@component
def poller(topic):
    delay, set_delay = use_state(0.2)
    polls, set_polls = use_state(0)

    async def loop():
        print(f"start polling {topic} delay={delay:.1f}s")
        try:
            while True:
                await asyncio.sleep(delay)
                print(f"tick {topic} delay={delay:.1f}s")
                # the loop is created once per run, so read state via an updater
                set_polls(lambda current: current + 1)
        except asyncio.CancelledError:
            print(f"stop polling {topic} delay={delay:.1f}s")
            raise

    # `delay` here means adjusting it cancels and recreates the whole loop
    use_async_effect(loop, dependencies=[topic, delay])

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
