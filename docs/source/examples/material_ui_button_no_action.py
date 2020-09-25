import idom

material_ui = idom.Module("@material-ui/core")
MaterialButton = material_ui.Import("Button", fallback="loading...")


@idom.element
def ViewMaterialButton():
    return MaterialButton({"color": "primary", "variant": "contained"}, "Hello World!")


idom.run(ViewMaterialButton)
