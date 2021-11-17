from pathlib import Path

from idom import component, run, web


file = Path(__file__).parent / "super_simple_chart.js"
ssc = web.module_from_file("super-simple-chart", file, fallback="⌛")
SuperSimpleChart = web.export(ssc, "SuperSimpleChart")


@component
def App():
    print(__name__)
    return SuperSimpleChart(
        {
            "data": [
                {"x": 1, "y": 2},
                {"x": 2, "y": 4},
                {"x": 3, "y": 7},
                {"x": 4, "y": 3},
                {"x": 5, "y": 5},
                {"x": 6, "y": 9},
                {"x": 7, "y": 6},
            ],
            "height": 300,
            "width": 500,
            "color": "royalblue",
            "lineWidth": 4,
            "axisColor": "silver",
        }
    )


run(App)
