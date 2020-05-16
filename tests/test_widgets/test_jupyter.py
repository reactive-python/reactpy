import time
from threading import Thread

import pytest
import flask
from sanic import response

import idom
from idom.server import find_available_port
from idom.widgets.jupyter import JupyterDisplay

from tests.conftest import ServerWithErrorCatch


@pytest.fixture(scope="module")
def server_type():
    class ServerWithJupyterWidgetClient(ServerWithErrorCatch):
        def _setup_application(self, app, config):
            super()._setup_application(app, config)

            @app.route("/__test_jupyter_widget_client__")
            async def jupyter_widget_client(request):
                widget = JupyterDisplay()
                return response.html(widget._repr_html_())

    return ServerWithJupyterWidgetClient


def test_jupyter_display_repr():
    assert (
        repr(JupyterDisplay(f"http://localhost:5000"))
        == """JupyterDisplay({"host": "localhost:5000", "protocol": "http:"}, path='')"""
    )


def test_cross_origin_jupyter_display(server, driver, driver_wait, mount, host, port):
    clicked = idom.Var(False)

    # we use flask here just because its easier to set up in a thread
    flask_host = "127.0.0.1"
    flask_port = find_available_port(flask_host)

    @idom.element
    async def SimpleButton(self):
        @idom.event
        async def on_click(event):
            clicked.set(True)

        return idom.html.button(
            {"id": "simple-button", "onClick": on_click}, "click me cross origin"
        )

    def run():
        """Runs flask using the JuptyerDisplay client"""

        flask_app = flask.Flask(__name__)

        @flask_app.route("/")
        def widget():
            widget = JupyterDisplay(f"http://{host}:{port}")
            return widget._repr_html_()

        @flask_app.route("/shutdown")
        def shutdown():
            stop = flask.request.environ.get("werkzeug.server.shutdown")
            stop()

        flask_app.run(host=flask_host, port=flask_port, debug=False)

    thread = Thread(target=run, daemon=True)
    thread.start()
    time.sleep(1)  # wait for server to start

    mount(SimpleButton)

    # switch to flask widget view
    driver.get(f"http://{flask_host}:{flask_port}/")

    client_button = driver.find_element_by_id("simple-button")
    client_button.click()

    driver_wait.until(lambda d: clicked.get())

    driver.get(f"http://{flask_host}:{flask_port}/shutdown")


def test_same_origin_jupyter_display(driver, driver_wait, mount, host, port):
    clicked = idom.Var(False)

    @idom.element
    async def SimpleButton(self):
        @idom.event
        async def on_click(event):
            clicked.set(True)

        return idom.html.button(
            {"id": "simple-button", "onClick": on_click}, "click me same origin"
        )

    mount(SimpleButton)
    driver.get(f"http://{host}:{port}/__test_jupyter_widget_client__")

    client_button = driver.find_element_by_id("simple-button")
    client_button.click()

    driver_wait.until(lambda d: clicked.get())
