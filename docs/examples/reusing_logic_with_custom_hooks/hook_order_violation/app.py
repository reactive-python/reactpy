"""Wrong: a hook called inside an `if` inside a custom Hook. Nothing raises —
the state slots below simply shift, and a value from one hook appears in
another.
"""

from reactpy import component, html, use_state


# start
def use_profile(show_nickname):
    name, set_name = use_state("name")
    if show_nickname:
        nickname, set_nickname = use_state("nickname")
    else:
        nickname = "-"
    # `bio` is the third hook when the branch is taken and the second when it
    # is not, so it inherits the slot that `nickname` used to own
    bio, set_bio = use_state("bio")
    return name, nickname, bio, set_bio


@component
def profile(show_nickname):
    name, nickname, bio, set_bio = use_profile(show_nickname)

    async def extend_bio(event):
        set_bio(f"{bio}!")

    return html.div(
        html.button({"onClick": extend_bio}, f"bio={bio}"),
        html.p(f"name={name} nickname={nickname}"),
    )


@component
def app():
    show, set_show = use_state(True)

    async def handle_show_click(e):
        set_show(not show)

    return html.div(
        html.button({"onClick": handle_show_click}, "toggle nickname"),
        profile(show),
    )
