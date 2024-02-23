from reactpy import component, html

# start
@component
def button(on_click, children):
	return html.button({"on_click": on_click}, children)

@component
def play_button(movie_name):
	def handle_play_click(event):
		print(f"Playing {movie_name}")
		
	return html.button({"on_click": handle_play_click}, f"Play {movie_name}")

@component
def upload_button():
	return html.button({"on_click": lambda event: print("Uploading!")})

@component
def toolbar():
	return html.div(
        play_button({"movie_name": "Kiki's Delivery Service"}),
        upload_button()
	)