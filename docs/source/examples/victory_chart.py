import idom

victory = idom.Module("victory")

VictoryBar = victory.Import("VictoryBar", fallback="loading...")

idom.run(VictoryBar, {"style": {"parent": {"width": "500px"}}})
