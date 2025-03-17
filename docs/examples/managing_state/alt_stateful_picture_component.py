from reactpy import component, event, hooks, html


# start
@component
def picture():
    is_active, set_is_active = hooks.use_state(False)

    if is_active:
        return html.div(
            {
                "className": "background",
                "onClick": lambda event: set_is_active(False),
            },
            html.img(
                {
                    "onClick": event(stop_propagation=True),
                    "className": "picture picture--active",
                    "alt": "Rainbow houses in Kampung Pelangi, Indonesia",
                    "src": "https://i.imgur.com/5qwVYb1.jpeg",
                }
            ),
        )
    else:
        return html.div(
            {"className": "background background--active"},
            html.img(
                {
                    "onClick": event(
                        lambda event: set_is_active(True), stop_propagation=True
                    ),
                    "className": "picture",
                    "alt": "Rainbow houses in Kampung Pelangi, Indonesia",
                    "src": "https://i.imgur.com/5qwVYb1.jpeg",
                }
            ),
        )
