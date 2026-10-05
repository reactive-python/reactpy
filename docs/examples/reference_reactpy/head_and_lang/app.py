from reactpy import component, html
from reactpy.executors.asgi import ReactPy


@component
def page():
    return html.div(html.h1("Hello"), html.p("Welcome to the app."))


# start
my_app = ReactPy(
    page,
    # Must be built with html.head(); any other tag raises ValueError.
    html_head=html.head(
        html.title("My ReactPy App"),
        html.meta({"name": "description", "content": "A ReactPy app"}),
    ),
    html_lang="fr",
    http_headers={"X-Frame-Options": "DENY"},
    # Rendered into the <body> before the mount point, on the server.
    prepend_body=html.header({"id": "nav"}, "Server-rendered navigation"),
)
