# ruff: noqa: INP001
from reactpy import component, html


def video(*_, **__): ...


@component
def video_list(videos, empty_heading):
    count = len(videos)
    heading = empty_heading
    if count > 0:
        noun = "Videos" if count > 1 else "Video"
        heading = f"{count} {noun}"

    return html.section(
        html.h2(heading),
        [video(x, key=x.id) for x in videos],
    )
