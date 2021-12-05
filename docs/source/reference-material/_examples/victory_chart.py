import idom


victory = idom.web.module_from_template("react", "victory-bar", fallback="⌛")
VictoryBar = idom.web.export(victory, "VictoryBar")

bar_style = {"parent": {"width": "500px"}, "data": {"fill": "royalblue"}}
idom.run(idom.component(lambda: VictoryBar({"style": bar_style})))
