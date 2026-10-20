"""Reset a form when the profile changes: render a key, not an Effect."""

from reactpy import component, html, use_state


# start
@component
def profile(user_id):
    # Any state declared here is thrown away whenever the key changes, along
    # with the state of every component below it. No Effect needed.
    comment, set_comment = use_state("")

    async def handle_comment_change(event):
        set_comment(await event.target.value)

    return html.div(
        html.h2(f"profile {user_id}"),
        html.textarea(
            {
                "value": comment,
                "placeholder": "leave a comment",
                "onChange": handle_comment_change,
            }
        ),
        html.p(f"draft: {comment or '(empty)'}"),
    )


@component
def profile_page():
    user_id, set_user_id = use_state("ada")

    async def handle_user_id_click(event):
        set_user_id("grace" if user_id == "ada" else "ada")

    return html.div(
        html.button(
            {"onClick": handle_user_id_click},
            "Next profile",
        ),
        # The key is what makes ReactPy treat this as a different profile.
        profile(user_id, key=user_id),
    )
