import idom

victory = idom.Module("victory", fallback="loading...")

VictoryBar = victory.Import("VictoryBar")

idom.run(
    idom.element(
        lambda: VictoryBar({"style": {"parent": {"width": "500px"}}}),
    )
)
