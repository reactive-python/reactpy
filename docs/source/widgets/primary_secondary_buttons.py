import idom

semantic_ui = idom.Module("semantic-ui-react")
Button = semantic_ui.Import("Button")

semantic_ui_style = idom.html.link(
    {
        "rel": "stylesheet",
        "href": "//cdn.jsdelivr.net/npm/semantic-ui@2.4.2/dist/semantic.min.css",
    }
)


def pre_seperated(*args):
    return idom.html.pre(
        {"style": {"white-space": "pre-wrap"}}, "\n".join(map(str, args))
    )


@idom.element
async def PrimarySecondaryButtons(self):
    state, set_state = idom.hooks.use_state(
        {"message": None, "event": None, "info": None}
    )

    async def on_click_primary(event, info):
        set_state({"message": "Primary Clicked:", "event": event, "info": info})

    async def on_click_secondary(event, info):
        set_state({"message": "Secondary Clicked:", "event": event, "info": info})

    return idom.html.div(
        [
            semantic_ui_style,
            Button({"primary": True, "onClick": on_click_primary}, ["Primary"]),
            Button({"secondary": True, "onClick": on_click_secondary}, ["Secondary"]),
            pre_seperated(state["message"], state["event"], state["info"]),
        ]
    )


display(PrimarySecondaryButtons)
