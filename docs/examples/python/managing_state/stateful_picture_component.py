from reactpy import component, event, hooks, html


# start
@component
def picture():
    is_active, set_is_active = hooks.use_state(False)
    background_class_name = "background"
    picture_class_name = "picture"

    if (is_active):
        picture_class_name += " picture--active"
    else:
        background_class_name += " background--active"
    
    @event(stop_propagation=True)
    def handle_click(event):
        set_is_active(True)

    return html.div(
        {
            "class_name": background_class_name,
            "on_click": set_is_active(False)
        },
        html.img(
            {
                "on_click": handle_click,
                "class_name": picture_class_name,
                "alt": "Rainbow houses in Kampung Pelangi, Indonesia",
                "src": "https://i.imgur.com/5qwVYb1.jpeg"
            }
        )
    )
