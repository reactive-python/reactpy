import idom

material_ui = idom.Module("@material-ui/core")
MaterialButton = material_ui.Import("Button", fallback="loading...")

display(MaterialButton, {"color": "primary", "variant": "contained"}, "Hello World!")
