import webbrowser
from typing import NoReturn

from . import html
from .core.component import component
from .core.vdom import VdomDict
from .server.utils import find_available_port, find_builtin_server_type


@component
def App() -> VdomDict:
    return html.div(
        {"style": {"padding": "15px", "border": "1px solid grey"}},
        html.h1("Sample Application"),
        html.p(
            "This is a basic application made with IDOM. Click ",
            html.a(
                {"href": "https://pypi.org/project/idom/", "target": "_blank"},
                "here",
            ),
            " to learn more.",
        ),
    )


def run_sample_app(open_browser: bool = False) -> NoReturn:
    """Run a sample application."""
    host = "127.0.0.1"
    port = find_available_port(host)
    server_type = find_builtin_server_type("PerClientStateServer")
    server = server_type(App)

    if not open_browser:
        server.run(host=host, port=port)
    else:
        thread = server.run_in_thread(host=host, port=port)
        server.wait_until_started(5)
        webbrowser.open(f"http://{host}:{port}")
        thread.join()
