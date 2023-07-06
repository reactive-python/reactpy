from reactpy import component, html, run
from reactpy.core.hooks import use_state, use_effect
from reactpy.backend.hooks import use_local_storage

@component
def App():
    storage = use_local_storage()
    key_input, set_key_input = use_state("")
    val_input, set_val_input = use_state("")

    @use_effect
    def handle_get():
        set_val_input(
            storage.get_item(
                key_input
            )
        )

    async def handle_set(e):
        await storage.set_item(
            key_input,
            val_input
        )

    return html.div(
        html.h1("Local Storage"),
        html.input(
            {
                "type": "text",
                "placeholder": "Key",
                "value": key_input,
                "on_change": lambda e: set_key_input(e["target"]["value"])
            }
        ),
        html.textarea(
            {
                "placeholder": "Value",
                "value": val_input,
                "on_change": lambda e: set_val_input(e["target"]["value"])
            }
        ),
        html.button(
            {
                "on_click": handle_get
            },
            "Get"
        ),
        html.button(
            {
                "on_click": handle_set
            },
            "Set"
        )
    )


run(App)
