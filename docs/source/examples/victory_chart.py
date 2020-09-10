import idom

from _utils import loading_spinner

victory = idom.Module("victory")

VictoryBar = victory.Import("VictoryBar", fallback=loading_spinner)

display(VictoryBar, {"style": {"parent": {"height": "100%"}}})
