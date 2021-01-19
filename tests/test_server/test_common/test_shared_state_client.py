from threading import Event
from weakref import finalize


import pytest

import idom
from idom.server import sanic as idom_sanic
from idom.testing import ServerMountPoint


@pytest.fixture(
    params=[
        # add new SharedClientStateServer implementations here to
        # run a suite of tests which check basic functionality
        idom_sanic.SharedClientStateServer,
    ],
    ids=lambda cls: f"{cls.__module__}.{cls.__name__}",
)
def server_mount_point(request):
    return ServerMountPoint(request.param, sync_views=True)


def test_shared_client_state(create_driver, mount, server_mount_point):
    driver_1 = create_driver()
    driver_2 = create_driver()
    was_garbage_collected = Event()

    @idom.element
    def IncrCounter(count=0):
        count, set_count = idom.hooks.use_state(count)

        @idom.event
        async def incr_on_click(event):
            set_count(count + 1)

        button = idom.html.button(
            {"onClick": incr_on_click, "id": "incr-button"}, "click to increment"
        )

        return idom.html.div(button, Counter(count))

    @idom.element
    def Counter(count):
        element = idom.hooks.current_hook().element
        finalize(element, was_garbage_collected.set)
        return idom.html.div({"id": f"count-is-{count}"}, count)

    mount(IncrCounter)

    driver_1.get(server_mount_point.url())
    driver_2.get(server_mount_point.url())

    client_1_button = driver_1.find_element_by_id("incr-button")
    client_2_button = driver_2.find_element_by_id("incr-button")

    driver_1.find_element_by_id("count-is-0")
    driver_2.find_element_by_id("count-is-0")

    client_1_button.click()

    driver_1.find_element_by_id("count-is-1")
    driver_2.find_element_by_id("count-is-1")

    client_2_button.click()

    driver_1.find_element_by_id("count-is-2")
    driver_2.find_element_by_id("count-is-2")

    assert was_garbage_collected.wait(1)


def test_shared_client_state_server_does_not_support_per_client_parameters(
    driver_get, last_server_error
):
    driver_get({"per_client_param": 1})

    error = last_server_error.current

    assert error is not None

    assert isinstance(error, ValueError)
    assert "does not support per-client view parameters" in str(error)

    last_server_error.current = None
