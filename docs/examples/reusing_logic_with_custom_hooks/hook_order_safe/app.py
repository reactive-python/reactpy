"""Correct: the hook always calls `use_state` the same number of times. The
branch only changes what is returned, so the slots stay put.
"""

from reactpy import component, html, use_state


# start
def use_profile(show_nickname):
    name, set_name = use_state("name")
    # the hook is called unconditionally; only the returned value is conditional
    nickname, set_nickname = use_state("nickname")
    bio, set_bio = use_state("bio")
    return name, (nickname if show_nickname else "-"), bio, set_bio


@component
def profile(show_nickname):
    name, nickname, bio, set_bio = use_profile(show_nickname)

    async def extend_bio(event):
        set_bio(bio + "!")

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
