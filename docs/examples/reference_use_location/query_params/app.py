from urllib.parse import parse_qs

from reactpy import component, html, use_location

# start


@component
def product_page():
    location = use_location()

    # `query_string` mirrors `window.location.search`, so it *keeps* the
    # leading "?". Strip it first or the first parameter gets a mangled name:
    # parse_qs("?tab=2&sort=price") yields the key "?tab", not "tab".
    params = parse_qs(location.query_string.lstrip("?"))
    tab = params.get("tab", ["overview"])[0]
    sort = params.get("sort", ["name"])[0]

    return html.div(
        html.h1(f"Products — {tab}"),
        html.p(f"sorted by: {sort}"),
        html.p(f"raw query string: {location.query_string!r}"),
        html.p(f"path: {location.path}"),
    )
