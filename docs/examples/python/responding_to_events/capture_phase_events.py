from reactpy import component, html

# start

html.div(
	{
		"on_click_capture": lambda event:
			# this runs first
	}
	html.button("on_click": lambda event: event.stop_propagation())
	html.button("on_click": lambda event: event.stop_propagation())
)
