import idom

# this may take a moment to download and install
victory = idom.Module("victory", install=True)

VictoryBar = victory.Import("VictoryBar")

display(VictoryBar, {"style": {"parent": {"width": "500px"}}})
