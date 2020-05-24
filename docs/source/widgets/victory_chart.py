import idom

victory = idom.Module("victory", install=True)
VictoryBar = victory.Import("VictoryBar")

display(VictoryBar, {"style": {"parent": {"width": "500px"}}})
