from __future__ import annotations

import sys

from common.github_utils import (
    REPO_NAME,
    date_range_query,
    last_release_date,
    search_idom_repo,
)


SECTION_FORMAT_TEMPLATES = {
    "md": lambda title: f"# {title}",
    "rst": lambda title: f"**{title}**",
    "text": lambda title: f"{title}\n{'-' * len(title)}",
}


ISSUE_FORMAT_TEMPLATES = {
    "md": lambda title, number, **_: f"- {title} - [#{number}](https://github.com/{REPO_NAME}/issues/{number})",
    "rst": lambda title, number, **_: f"- {title} - :pull:`{number}`",
    "text": lambda title, number, **_: f"- {title} - #{number}",
}

PULL_REQUEST_FORMAT_TEMPLATES = {
    "md": lambda title, number, **_: f"- {title} - [#{number}](https://github.com/{REPO_NAME}/pull/{number})",
    "rst": lambda title, number, **_: f"- {title} - :issue:`{number}`",
    "text": lambda title, number, **_: f"- {title} - #{number}",
}


def show_issues(format: str):
    print(SECTION_FORMAT_TEMPLATES[format]("Closed Issues"))
    template = ISSUE_FORMAT_TEMPLATES[format]
    query = f"type:issue closed:{date_range_query(last_release_date())}"
    for issue in search_idom_repo(query):
        print(template(**issue))


def show_pull_requests(format: str = "text"):
    print(SECTION_FORMAT_TEMPLATES[format]("Merged Pull Requests"))
    template = PULL_REQUEST_FORMAT_TEMPLATES[format]
    query = f"type:pr merged:{date_range_query(last_release_date())}"
    for pull in search_idom_repo(query):
        print(template(**pull))


def main(format: str = "text"):
    for func in [show_issues, show_pull_requests]:
        func(format)
        print()


if __name__ == "__main__":
    main(*sys.argv[1:])
