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
async def EventLog(self, event=None):
    return idom.html.div(
        {"class": "highlight"}, idom.html.pre(json.dumps(event, indent=2))
    )


@idom.element
async def ShowChartClicks(self):

    log = EventLog({})

    async def log_event(event):
        log.update(event)

    return idom.html.div(
        ClickableChart(
            {
                "data": data,
                "onClick": log_event,
                "style": {"parent": {"width": "500px"}},
            },
        ),
        log,
    )


display(ShowChartClicks)
