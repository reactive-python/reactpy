from reactpy import component, html

# start
def button(on_click, children): 
	return html.button(
			{"on_click": lambda event: event.stop_propagation()},
			on_click,
			f"children")

def toolbar():
	return html.div(
			{
				"class_name": "Toolbar",
				"on_click": lambda event: print("You clicked on the toolbar!")
			},
			html.button({"on_click": lambda event: print("Playing!")}, "Play Movie"),
			html.button({"on_click": lambda event: print("Uploading!")}, "Upload Image")
		)
