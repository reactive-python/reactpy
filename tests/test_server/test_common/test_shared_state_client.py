from threading import Event
from weakref import finalize

import pytest

import idom
from idom.server import fastapi as idom_fastapi
from idom.server import sanic as idom_sanic
from idom.server import starlette as idom_starlette
from idom.testing import ServerMountPoint


@pytest.fixture(
    params=[
        # add new SharedClientStateServer implementations here to
        # run a suite of tests which check basic functionality
        idom_sanic.SharedClientStateServer,
        idom_fastapi.SharedClientStateServer,
        idom_starlette.SharedClientStateServer,
    ],
    ids=lambda cls: f"{cls.__module__}.{cls.__name__}",
)
def server_mount_point(request):
    with ServerMountPoint(request.param, sync_views=True) as mount_point:
        yield mount_point


def test_shared_client_state(create_driver, server_mount_point):
    was_garbage_collected = Event()

    @idom.component
    def IncrCounter():
        count, set_count = idom.hooks.use_state(0)

        def incr_on_click(event):
            set_count(count + 1)

        button = idom.html.button(
            {"onClick": incr_on_click, "id": "incr-button"}, "click to increment"
        )

        counter = Counter(count)
        finalize(counter, was_garbage_collected.set)

        return idom.html.div(button, counter)

    @idom.component
    def Counter(count):
        return idom.html.div({"id": f"count-is-{count}"}, count)

    server_mount_point.mount(IncrCounter)

    driver_1 = create_driver()
    driver_2 = create_driver()

    driver_1.get(server_mount_point.url())
    driver_2.get(server_mount_point.url())

    client_1_button = driver_1.find_element("id", "incr-button")
    client_2_button = driver_2.find_element("id", "incr-button")

    driver_1.find_element("id", "count-is-0")
    driver_2.find_element("id", "count-is-0")

    client_1_button.click()

    driver_1.find_element("id", "count-is-1")
    driver_2.find_element("id", "count-is-1")

    client_2_button.click()

    driver_1.find_element("id", "count-is-2")
    driver_2.find_element("id", "count-is-2")

    assert was_garbage_collected.wait(1)
    was_garbage_collected.clear()

    # Ensure this continues working after a refresh. In the past dispatchers failed to
    # exit when the connections closed. This was due to an expected error that is raised
    # when the web socket closes.
    driver_1.refresh()
    driver_2.refresh()

    client_1_button = driver_1.find_element("id", "incr-button")
    client_2_button = driver_2.find_element("id", "incr-button")

    client_1_button.click()

    driver_1.find_element("id", "count-is-3")
    driver_2.find_element("id", "count-is-3")

    client_1_button.click()

    driver_1.find_element("id", "count-is-4")
    driver_2.find_element("id", "count-is-4")

    client_2_button.click()

    assert was_garbage_collected.wait(1)


def test_shared_client_state_server_does_not_support_per_client_parameters(
    driver_get,
    driver_wait,
    server_mount_point,
):
    driver_get(
        {
            "per_client_param": 1,
            # we need to stop reconnect attempts to prevent the error from happening
            # more than once
            "noReconnect": True,
        }
    )

    driver_wait.until(
        lambda driver: (
            len(
                server_mount_point.list_logged_exceptions(
                    "does not support per-client view parameters", ValueError
                )
            )
            == 1
        )
    )
