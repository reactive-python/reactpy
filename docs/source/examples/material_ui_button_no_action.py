import idom

material_ui = idom.Module("@material-ui/core")
MaterialButton = material_ui.Import("Button", fallback="loading...")

idom.run(
    idom.element(
        lambda: MaterialButton(
            {"color": "primary", "variant": "contained"}, "Hello World!"
        )
    )
)
