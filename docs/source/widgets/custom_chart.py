import json
from pathlib import Path

import idom


here = Path(__file__).parent
custom_chart_path = here / "custom_chart.js"
ClickableChart = idom.Module("chart", source=custom_chart_path).Import("ClickableChart")


data = [
    {"x": 1, "y": 2},
    {"x": 2, "y": 4},
    {"x": 3, "y": 7},
    {"x": 4, "y": 3},
    {"x": 5, "y": 5},
]


@idom.element
async def ShowChartClicks():
    shared_last_event = idom.hooks.Shared({})
    idom.html.div(
        CustomChart(shared_last_event), LastEventView(shared_last_event),
    )


@idom.element
async def Chart(shared_last_event):
    set_last_event = idom.hooks.use_state(shared_last_event)[1]

    async def log_event(event):
        set_last_event(event)

    return ClickableChart(
        {"data": data, "onClick": log_event, "style": {"parent": {"width": "500px"}}},
    )


@idom.element
async def LastEventView(shared_last_event):
    last_event = idom.hooks.use_state(shared_last_event)[0]

    return idom.html.div(
        {"class": "highlight"}, idom.html.pre(json.dumps(last_event, indent=2))
    )


display(ShowChartClicks)
