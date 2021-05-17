from threading import Event

import pytest

from idom.server.utils import find_available_port, poll, wait_on_event


def test_poll():
    with pytest.raises(TimeoutError, match="Did not do something within 0.1 seconds"):
        poll("do something", 0.01, 0.1, lambda: False)
    poll("do something", 0.01, None, [True, False, False].pop)


def test_wait_on_event():
    event = Event()
    with pytest.raises(TimeoutError, match="Did not do something within 0.1 seconds"):
        wait_on_event("do something", event, 0.1)
    event.set()
    wait_on_event("do something", event, None)


def test_find_available_port():
    assert find_available_port("localhost", port_min=5000, port_max=6000)
    with pytest.raises(RuntimeError, match="no available port"):
        # check that if port range is exhausted we raise
        find_available_port("localhost", port_min=0, port_max=0)
