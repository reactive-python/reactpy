from data import contacts

from reactpy import component, html, use_state


# start
@component
def chat(contact):
    draft, set_draft = use_state("")

    async def handle_draft_click(event):
        set_draft("")

    return html.section(
        {"className": "chat"},
        html.h3(f"To: {contact['name']} <{contact['email']}>"),
        html.textarea({"placeholder": "Write a message", "value": draft}),
        html.button({"onClick": handle_draft_click}, "Clear"),
    )


@component
def contact_list(selected_contact, on_select):
    def make_select(contact):
        # A factory, not a lambda: a handler must be a coroutine, and the
        # contact it acts on is bound by the closure.
        async def choose(event):
            on_select(contact)

        return choose

    return html.section(
        {"className": "contact-list"},
        html.ul(
            [
                html.li(
                    {"key": contact["id"]},
                    html.button(
                        {"onClick": make_select(contact)},
                        contact["name"],
                    ),
                )
                for contact in contacts
            ]
        ),
    )


@component
def messenger():
    to, set_to = use_state(contacts[0])

    return html.div(
        contact_list(to, set_to),
        # Without the key, switching contacts keeps the half-written message,
        # because chat() stays at the same position. The key ties the draft to
        # the contact instead of the slot.
        chat(to, key=f"chat-{to['id']}"),
    )
