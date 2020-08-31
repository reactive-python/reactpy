import asyncio
import random
import time

import idom
from idom.widgets.html import Input


VictoryLine = idom.Module("victory").Import("VictoryLine")


@idom.element
async def RandomWalk():
    mu = idom.hooks.use_ref(0)
    sigma = idom.hooks.use_ref(1)

    mu_inputs = number_inputs("Mean", mu.current, mu.set, (-1, 1, 0.01))
    sigma_inputs = number_inputs(
        "Standard Deviation", sigma.current, sigma.set, (0, 1, 0.01)
    )

    interval = use_interval(0.4)
    data, set_data = idom.hooks.use_state([{"x": 0, "y": 0}] * 50)

    @use_async_effect
    async def animate():
        await interval
        last_data_point = data[-1]
        next_data_point = {
            "x": last_data_point["x"] + 1,
            "y": last_data_point["y"] + random.gauss(mu.current, sigma.current),
        }
        set_data(data[1:] + [next_data_point])

    style = idom.html.style(
        [
            """
            .number-inputs {margin-bottom: 20px}
            .number-inputs input {width: 48%;float: left}
            .number-inputs input + input {margin-left: 4%}
            """
        ]
    )

    return idom.html.div(
        VictoryLine({"data": data, "style": {"parent": {"width": "500px"}}}),
        style,
        mu_inputs,
        sigma_inputs,
    )


def number_inputs(label, value, callback, domain):
    value, set_value = idom.hooks.use_state(value)

    def update_value(value):
        set_value(value)
        callback(value)

    minimum, maximum, step = domain
    attrs = {"min": minimum, "max": maximum, "step": step}
    return idom.html.fieldset(
        {"class": "number-inputs"},
        [idom.html.legend({"style": {"font-size": "medium"}}, label)],
        Input(update_value, "number", value, attributes=attrs, cast=float),
        Input(update_value, "range", value, attributes=attrs, cast=float),
    )


def use_async_effect(function):
    def ensure_effect_future():
        future = asyncio.ensure_future(function())
        return future.cancel

    idom.hooks.use_effect(ensure_effect_future)


def use_interval(rate):
    usage_time = idom.hooks.use_ref(time.time())

    async def interval():
        await asyncio.sleep(rate - (time.time() - usage_time.current))
        usage_time.current = time.time()

    return interval()


display(RandomWalk)
