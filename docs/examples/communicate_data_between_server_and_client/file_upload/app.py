from reactpy import component, html, use_state

# start
READ_FILE = (
    "const file = event.target.files[0];"
    "if (file) {"
    "    file.text().then((text) => {"
    "        document.getElementById('payload').value = text;"
    "    });"
    "}"
)


@component
def text_upload():
    received, set_received = use_state("Choose a file, then send.")

    async def handle_submit(event):
        event.preventDefault()
        # Ask for the collection which exists for this purpose: an
        # HTMLFormControlsCollection is iterable, so the client hands it
        # over as a list - one dict per control, named or not.
        controls = await event.target.elements
        payload = next(
            (c["value"] for c in controls if c.get("name") == "payload"),
            "",
        )
        set_received(f"{len(payload)} characters received")

    return html.form(
        {"onSubmit": handle_submit},
        html.input({"type": "file", "onChange": READ_FILE}),
        html.input({"type": "hidden", "id": "payload", "name": "payload", "value": ""}),
        html.button({"type": "submit"}, "Send"),
        html.pre(received),
    )


# end
