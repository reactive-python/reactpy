import idom

victory = idom.Module("victory")

VictoryBar = victory.Import("VictoryBar", fallback="loading...")

idom.run(
    idom.element(
        lambda: VictoryBar({"style": {"parent": {"width": "500px"}}}),
    )
)
