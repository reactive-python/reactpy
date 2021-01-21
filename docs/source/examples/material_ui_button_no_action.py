import idom

material_ui = idom.install("@material-ui/core", fallback="loading...")

idom.run(
    idom.component(
        lambda: material_ui.Button(
            {"color": "primary", "variant": "contained"}, "Hello World!"
        )
    )
)
