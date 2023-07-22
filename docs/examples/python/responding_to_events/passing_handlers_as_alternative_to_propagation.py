from reactpy import component, html

# start
def button(on_click, children):
	return html.button(
			{
				"on_click": lambda event: 
                    event.stop_propagation()
				    on_click
			},
            f"{children}"
		)