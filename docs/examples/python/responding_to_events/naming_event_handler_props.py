from reactpy import component, html

# start
@component
def button(on_smash, children):
	return html.button({"on_click": on_smash}, f"children")

@component
def app():
	return html.div(
		html.button({"on_smash": lambda event: print("Playing!")}, "Play Movie"), 
		html.button({"on_smash": lambda event: print("Uploading!")}, "Upload Image")
    )