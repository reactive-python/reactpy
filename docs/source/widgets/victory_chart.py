import idom

victory = idom.Module("victory")

VictoryBar = victory.Import("VictoryBar")

display(VictoryBar, {"style": {"parent": {"width": "500px"}}})
