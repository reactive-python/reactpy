from pathlib import Path

import idom


file = Path(__file__).parent / "super_simple_chart.js"
ssc = idom.web.module_from_file("super-simple-chart", file, fallback="⌛")
SuperSimpleChart = idom.web.export(ssc, "SuperSimpleChart")

idom.run(
    idom.component(
        lambda: SuperSimpleChart(
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
    )
)
