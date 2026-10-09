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

    def handle_submit(event):
        event.preventDefault()
        # On submit, target is the list of *named* controls in the form.
        controls = event["target"]
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
