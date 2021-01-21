import idom

victory = idom.install("victory", fallback="loading...")

idom.run(
    idom.component(
        lambda: victory.VictoryBar({"style": {"parent": {"width": "500px"}}}),
    )
)
