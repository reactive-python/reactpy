
from reactpy import component, html

# start
def signup():
	return html.form(
			{
				"on_submit":
				lambda event: event.prevent_default()
				    print("Submitting")
			},
			html.input(),
			html.button("Send")
		)