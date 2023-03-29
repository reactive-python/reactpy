import asyncio
import random
import time

import reactpy
from reactpy.widgets import Input


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
