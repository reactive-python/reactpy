from reactpy import component, html

# start
def light_switch():
	def handle_click():
		body_style = document.body.style
		if body_style.background_color == "black":
			body_style.background_color = "white"
		else:
			body_style.background_color = "black"
	return html.button({"on_click": lambda event: handle_click()}, "Toggle the lights")

