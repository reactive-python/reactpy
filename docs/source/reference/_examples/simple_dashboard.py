import asyncio
import random
import time

import reactpy
from reactpy.widgets import Input

victory = reactpy.web.module_from_template(
    "react",
    "victory-line",
    fallback="⌛",
    # not usually required (see issue #461 for more info)
    unmount_before_update=True,
)
VictoryLine = reactpy.web.export(victory, "VictoryLine")


@reactpy.component
def RandomWalk():
    mu = reactpy.hooks.use_ref(0)
    sigma = reactpy.hooks.use_ref(1)

    return reactpy.html.div(
        RandomWalkGraph(mu, sigma),
        reactpy.html.style(
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


@reactpy.component
def RandomWalkGraph(mu, sigma):
    interval = use_interval(0.5)
    data, set_data = reactpy.hooks.use_state([{"x": 0, "y": 0}] * 50)

    @reactpy.hooks.use_async_effect
    async def animate():
        await interval
        last_data_point = data[-1]
        next_data_point = {
            "x": last_data_point["x"] + 1,
            "y": last_data_point["y"] + random.gauss(mu.current, sigma.current),
        }
        set_data(data[1:] + [next_data_point])

    return VictoryLine(
        {
            "data": data,
            "style": {
                "parent": {"width": "100%"},
                "data": {"stroke": "royalblue"},
            },
        }
    )


@reactpy.component
def NumberInput(label, value, set_value_callback, domain):
    minimum, maximum, step = domain
    attrs = {"min": minimum, "max": maximum, "step": step}

    value, set_value = reactpy.hooks.use_state(value)

    def update_value(value):
        set_value(value)
        set_value_callback(value)

    return reactpy.html.fieldset(
        {"class_name": "number-input-container"},
        reactpy.html.legend({"style": {"font-size": "medium"}}, label),
        Input(update_value, "number", value, attributes=attrs, cast=float),
        Input(update_value, "range", value, attributes=attrs, cast=float),
    )


def use_interval(rate):
    usage_time = reactpy.hooks.use_ref(time.time())

    async def interval() -> None:
        await asyncio.sleep(rate - (time.time() - usage_time.current))
        usage_time.current = time.time()

    return asyncio.ensure_future(interval())


reactpy.run(RandomWalk)
