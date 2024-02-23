from reactpy import component, html

# start
def color_switch(onChangeColor):
	return html.button({"on_click": lambda event:
			event.stop_propagation
			on_change_color()
		}, "Change color")	
