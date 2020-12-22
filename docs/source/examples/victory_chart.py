import idom

victory = idom.install("victory")
VictoryBar = victory.define("VictoryBar", fallback="loading...")

idom.run(
    idom.element(
        lambda: VictoryBar({"style": {"parent": {"width": "500px"}}}),
    )
)
