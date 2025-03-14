# ruff: noqa: INP001
from reactpy import component, html, use_state


def filter_videos(*_, **__):
    return []


def search_input(*_, **__): ...


def video_list(*_, **__): ...


@component
def searchable_video_list(videos):
    search_text, set_search_text = use_state("")
    found_videos = filter_videos(videos, search_text)

    return html._(
        search_input(
            {"onChange": lambda event: set_search_text(event["target"]["value"])},
            value=search_text,
        ),
        video_list(
            videos=found_videos,
            empty_heading=f"No matches for “{search_text}”",
        ),
    )
