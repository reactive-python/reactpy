import idom


victory = idom.install("victory", fallback="loading...")
bar_style = {"parent": {"width": "500px"}, "data": {"fill": "royalblue"}}
idom.run(idom.component(lambda: victory.VictoryBar({"style": bar_style})))
