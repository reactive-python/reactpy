import reactpy


victory = reactpy.web.module_from_template("react", "victory-bar", fallback="⌛")
VictoryBar = reactpy.web.export(victory, "VictoryBar")

bar_style = {"parent": {"width": "500px"}, "data": {"fill": "royalblue"}}
reactpy.run(reactpy.component(lambda: VictoryBar({"style": bar_style})))
