from __future__ import annotations

import sys
from datetime import datetime
from typing import Any, Iterator

import requests
from dateutil.parser import isoparse


REPO = "idom-team/idom"
STR_DATE_FORMAT = r"%Y-%m-%d"


def last_release() -> datetime:
    response = requests.get(f"https://api.github.com/repos/{REPO}/releases/latest")
    return isoparse(response.json()["published_at"])


def pull_requests_after(date: datetime) -> Iterator[Any]:
    then = date.strftime(STR_DATE_FORMAT)
    now = datetime.now().strftime(STR_DATE_FORMAT)
    query = f"repo:{REPO} type:pr merged:{then}..{now}"

    page = 0
    while True:
        page += 1
        response = requests.get(
            "https://api.github.com/search/issues",
            {"q": query, "per_page": 15, "page": page},
        )

        response_json = response.json()

        if response_json["incomplete_results"]:
            raise RuntimeError(response)

        items = response_json["items"]
        if items:
            yield from items
        else:
            break


FORMAT_TEMPLATES = {
    "md": f"- {{title}} - [#{{number}}](https://github.com/{REPO}/pull/{{number}})",
    "rst": "- {title} - :pull:`{number}`",
    "text": "- {title} - #{number}",
}


def main(format: str = "text"):
    template = FORMAT_TEMPLATES[format]
    for pr in pull_requests_after(last_release()):
        print(template.format(**pr))


if __name__ == "__main__":
    main(*sys.argv[1:])
