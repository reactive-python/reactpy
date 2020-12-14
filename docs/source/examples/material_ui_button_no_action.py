import idom

material_ui = idom.install("@material-ui/core")
MaterialButton = material_ui.use("Button", fallback="loading...")

idom.run(
    idom.element(
        lambda: MaterialButton(
            {"color": "primary", "variant": "contained"}, "Hello World!"
        )
    )
)
