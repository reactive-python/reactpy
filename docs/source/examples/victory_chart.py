import idom

victory = idom.install("victory", fallback="loading...")

idom.run(
    idom.element(
        lambda: victory.VictoryBar({"style": {"parent": {"width": "500px"}}}),
    )
)
