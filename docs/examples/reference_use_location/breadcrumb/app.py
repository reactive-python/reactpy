from reactpy import component, html, use_location

# start


@component
def breadcrumb():
    location = use_location()

    # `path` mirrors `window.location.pathname`, so a component rendered on the
    # ReactPy server can describe the page the browser is actually on -- useful
    # for navigation that needs to know where it is.
    parts = [part for part in location.path.split("/") if part]

    return html.nav(
        html.a({"href": "/"}, "home"),
        *[
            html.span(" / ", html.a({"href": "/" + "/".join(parts[: i + 1])}, part))
            for i, part in enumerate(parts)
        ],
    )
