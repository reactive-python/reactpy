import asyncio
import random
import time

import idom
from idom.widgets.html import Input

victory = idom.install("victory", fallback="loading...")


@idom.component
def RandomWalk():
    mu = idom.hooks.use_ref(0)
    sigma = idom.hooks.use_ref(1)

    return idom.html.div(
        RandomWalkGraph(mu, sigma),
        idom.html.style(
            """
            .number-input-container {margin-bottom: 20px}
            .number-input-container input {width: 48%;float: left}
            .number-input-container input + input {margin-left: 4%}
            """
        ),
        NumberInput(
            "Mean",
            mu.current,
            mu.set_current,
            (-1, 1, 0.01),
        ),
        NumberInput(
            "Standard Deviation",
            sigma.current,
            sigma.set_current,
            (0, 1, 0.01),
        ),
    )


@idom.component
def RandomWalkGraph(mu, sigma):
    interval = use_interval(0.5)
    data, set_data = idom.hooks.use_state([{"x": 0, "y": 0}] * 50)

    @idom.hooks.use_effect
    async def animate():
        await interval
        last_data_point = data[-1]
        next_data_point = {
            "x": last_data_point["x"] + 1,
            "y": last_data_point["y"] + random.gauss(mu.current, sigma.current),
        }
        set_data(data[1:] + [next_data_point])

    return victory.VictoryLine({"data": data, "style": {"parent": {"width": "500px"}}})


@idom.component
def NumberInput(label, value, set_value_callback, domain):
    minimum, maximum, step = domain
    attrs = {"min": minimum, "max": maximum, "step": step}

    value, set_value = idom.hooks.use_state(value)

    def update_value(value):
        set_value(value)
        set_value_callback(value)

    return idom.html.fieldset(
        {"class": "number-input-container"},
        [idom.html.legend({"style": {"font-size": "medium"}}, label)],
        Input(update_value, "number", value, attributes=attrs, cast=float),
        Input(update_value, "range", value, attributes=attrs, cast=float),
    )


def use_interval(rate):
    usage_time = idom.hooks.use_ref(time.time())

    async def interval() -> None:
        await asyncio.sleep(rate - (time.time() - usage_time.current))
        usage_time.current = time.time()

    return asyncio.ensure_future(interval())


idom.run(RandomWalk)
