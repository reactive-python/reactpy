from reactpy import component, event, hooks, html


# start
@component
def picture():
    is_active, set_is_active = hooks.use_state(False)

    if (is_active):
        return html.div(
            {
                "class_name": "background",
                "on_click": lambda event: set_is_active(False)
            },
            html.img(
                {
                    "on_click": event(stop_propagation=True),
                    "class_name": "picture picture--active",
                    "alt": "Rainbow houses in Kampung Pelangi, Indonesia",
                    "src": "https://i.imgur.com/5qwVYb1.jpeg"
                }
            )
        )
    else:
        return html.div(
            {
                "class_name": "background background--active"
            },
            html.img(
                {
                    "on_click": event(lambda event: set_is_active(True),
                                    stop_propagation=True),
                    "class_name": "picture",
                    "alt": "Rainbow houses in Kampung Pelangi, Indonesia",
                    "src": "https://i.imgur.com/5qwVYb1.jpeg"
                }
            )
        )