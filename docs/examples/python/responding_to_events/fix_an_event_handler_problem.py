from reactpy import component, html

# start

def light_switch():
	def handle_click():
		body_style = document.body.style
		if bodyStyle.backgroundColor == "black":
			bodyStyle.backgroundColor = "white"
		else:
			bodyStyle.backgroundColor = "black"

	return html.button({"on_click": handleClick()}, "Toggle the lights")