from reactpy import component, html

# start
def app():
	return toolbar({
		"on_play_movie": lambda event: print("Playing!"),
		"on_upload_image": lambda event: print("Uploading!")
	})

def toolbar(on_play_movie, on_upload_image):
	return html.div(
		html.button({"on_click": on_play_movie}, "Play Movie"),
		html.button({"on_click": on_upload_image}, "Upload Image")
	)

def button(on_click, children):
	return html.button({"on_click": on_click}, f"children")
