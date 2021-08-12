from __future__ import annotations

import sys

from common.github_utils import (
    REPO_NAME,
    date_range_query,
    last_release_date,
    search_idom_repo,
)


FORMAT_TEMPLATES = {
    "md": f"- {{title}} - [#{{number}}](https://github.com/{REPO_NAME}/issues/{{number}})",
    "rst": "- {title} - :issue:`{number}`",
    "text": "- {title} - #{number}",
}


def main(format: str = "text"):
    template = FORMAT_TEMPLATES[format]
    query = f"type:issue closed:{date_range_query(last_release_date())}"
    for pr in search_idom_repo(query):
        print(template.format(**pr))


if __name__ == "__main__":
    main(*sys.argv[1:])
