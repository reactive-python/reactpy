# import json
# from pathlib import Path

# import idom


# here = Path(__file__).parent
# custom_chart_path = here / "custom_chart.js"
# custom_chart = idom.Module("chart", source_file=custom_chart_path)
# ClickableChart = custom_chart.Import("ClickableChart")


# data = [
#     {"x": 1, "y": 2},
#     {"x": 2, "y": 4},
#     {"x": 3, "y": 7},
#     {"x": 4, "y": 3},
#     {"x": 5, "y": 5},
# ]


# @idom.element
# def ShowChartClicks():
#     last_event, set_last_event = idom.hooks.use_state({})
#     return idom.html.div(
#         ClickableChart(
#             {
#                 "data": data,
#                 "onClick": set_last_event,
#                 "style": {"parent": {"width": "500px"}},
#             },
#         ),
#         idom.html.div(
#             {"class": "highlight"},
#             idom.html.pre(json.dumps(last_event, indent=2)),
#         ),
#     )


# idom.run(ShowChartClicks)
