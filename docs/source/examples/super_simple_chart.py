from pathlib import Path

import idom


path_to_source_file = Path(__file__).parent / "super_simple_chart.js"
super_simple_chart = idom.Module("super-simple-chart", source_file=path_to_source_file)
SuperSimpleChart = super_simple_chart.define("SuperSimpleChart")


idom.run(
    idom.element(
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
                "color": "#24909d",
                "lineWidth": 4,
                "axisColor": "#bdc3c7",
            }
        )
    )
)
