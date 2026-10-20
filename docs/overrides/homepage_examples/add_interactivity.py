from reactpy import component, html, use_state


def filter_videos(*_, **__):
    return []


def search_input(*_, **__): ...


def video_list(*_, **__): ...


@component
def searchable_video_list(videos):
    search_text, set_search_text = use_state("")
    found_videos = filter_videos(videos, search_text)

    async def handle_search_change(event):
        set_search_text(await event.target.value)

    return html.fragment(
        search_input(
            {"onChange": handle_search_change},
            value=search_text,
        ),
        video_list(
            videos=found_videos,
            empty_heading=f"No matches for “{search_text}”",
        ),
    )
