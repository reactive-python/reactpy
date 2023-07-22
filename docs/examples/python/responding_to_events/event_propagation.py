from reactpy import component, html

# start
def toolbar():
	return (
		html.div(
			{
				"className": "Toolbar",
				"on_click": lambda event: print("You clicked on the toolbar!")
			},
			html.button({"on_click": lambda event: print("Playing")}, "Play Movie"),
			html.button({"on_click": lambda event: print("Uploading")}, "Upload Image")
		)
	)