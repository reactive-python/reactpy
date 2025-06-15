from reactpy import component, event, hooks, html


# start
@component
def picture():
    is_active, set_is_active = hooks.use_state(False)
    background_className = "background"
    picture_className = "picture"

    if is_active:
        picture_className += " picture--active"
    else:
        background_className += " background--active"

    @event(stop_propagation=True)
    def handle_click(event):
        set_is_active(True)

    return html.div(
        {"className": background_className, "onClick": set_is_active(False)},
        html.img(
            {
                "onClick": handle_click,
                "className": picture_className,
                "alt": "Rainbow houses in Kampung Pelangi, Indonesia",
                "src": "https://i.imgur.com/5qwVYb1.jpeg",
            }
        ),
    )
