import asyncio
from datetime import datetime, timezone

from reactpy import component, html, use_async_effect, use_state

# start


@component
def clock(color, time):
    return html.h1({"style": {"color": color}}, time)


@component
def app():
    color, set_color = use_state("lightcoral")
    now, set_now = use_state(datetime.now(timezone.utc))

    async def tick():
        while True:
            await asyncio.sleep(1)
            set_now(datetime.now(timezone.utc))

    use_async_effect(tick, dependencies=[])

    def handle_change(event):
        set_color(event["target"]["value"])

    return html.div(
        html.p(
            "Pick a color: ",
            html.select(
                {"value": color, "onChange": handle_change},
                html.option({"value": "lightcoral"}, "lightcoral"),
                html.option({"value": "midnightblue"}, "midnightblue"),
                html.option({"value": "rebeccapurple"}, "rebeccapurple"),
            ),
        ),
        clock(color=color, time=now.strftime("%H:%M:%S")),
    )
