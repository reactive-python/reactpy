from reactpy import component, html

# start
@component
def alert_button(message, children):
	return html.button({"on_click": lambda event: print(message)}, f"children")

@component
def toolbar():
	return html.div(
		alert_button({"message": "Playing!"}, "Play Movie"),
		alert_button({"message": "Uploading!"}, "Upload Image")
	)