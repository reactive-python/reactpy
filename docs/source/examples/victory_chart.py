import idom

victory = idom.Module("victory")

VictoryBar = victory.Import("VictoryBar", fallback=idom.html.h1("loading..."))

display(VictoryBar, {"style": {"parent": {"width": "500px"}}})
