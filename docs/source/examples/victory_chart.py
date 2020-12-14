import idom

victory = idom.install("victory")
VictoryBar = victory.use("VictoryBar", fallback="loading...")

idom.run(
    idom.element(
        lambda: VictoryBar({"style": {"parent": {"width": "500px"}}}),
    )
)
