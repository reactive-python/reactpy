import asyncio
import random
import time

import idom
from idom.widgets import Input


victory = idom.web.module_from_template(
    "react",
    "victory-line",
    fallback="⌛",
    # not usually required (see issue #461 for more info)
    unmount_before_update=True,
)
VictoryLine = idom.web.export(victory, "VictoryLine")


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

    return VictoryLine(
        {
            "data": data,
            "style": {
                "parent": {"width": "100%"},
                "data": {"stroke": "royalblue"},
            },
        }
    )


@idom.component
def NumberInput(label, value, set_value_callback, domain):
    minimum, maximum, step = domain
    attrs = {"min": minimum, "max": maximum, "step": step}

    value, set_value = idom.hooks.use_state(value)

    def update_value(value):
        set_value(value)
        set_value_callback(value)

    return idom.html.fieldset(
        idom.html.legend(label, style={"font_size": "medium"}),
        Input(update_value, "number", value, attributes=attrs, cast=float),
        Input(update_value, "range", value, attributes=attrs, cast=float),
        class_name="number-input-container",
    )


def use_interval(rate):
    usage_time = idom.hooks.use_ref(time.time())

    async def interval() -> None:
        await asyncio.sleep(rate - (time.time() - usage_time.current))
        usage_time.current = time.time()

    return asyncio.ensure_future(interval())


idom.run(RandomWalk)
