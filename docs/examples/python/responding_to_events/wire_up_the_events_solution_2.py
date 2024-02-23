from reactpy import component, html
from reactpy import use_state
from "./ColorSwitch" import color_switch

# start
@component
def app():
	clicks, setClicks = useState(0)

	def handle_click_outside():
		set_clicks(lambda c: c + 1)
	

	def get_random_light_color():
		r = 150 + math.round(100 * math.random())
		g = 150 + math.round(100 * math.random())
		b = 150 + math.round(100 * math.random())
		return f"rgb({r}, {g}, {b})"

	def handle_change_color():
		body_style = document.body.style
		body_style.background_color = get_random_light_color()

	return html.div(
        {
            "style": {
                "width": "100%",
                "height": "100%"
            },
            "on_click":"handle_click_outside"
        },
        color_switch(
            {"on_change_color": handle_change_color}
        ),
        html.br()
        html.br()
        html.h2(f"Clicks on page: {clicks}")