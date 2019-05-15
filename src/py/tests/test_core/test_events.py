import pytest

import idom
from idom.core.events import EventHandler


def test_simple_events():
    events = idom.Events()

    @events.on("Click")
    async def click_handler():
        pass

    @events.on("keyPress")
    async def key_press_handler():
        pass

    assert isinstance(events["onClick"], EventHandler)
    assert isinstance(events["onKeyPress"], EventHandler)


def test_event_handler_serialization():
    def handler(key, value):
        return (key, value)

    event_handler = EventHandler("onKeyPress", "uuid").add(
        handler, "value=target.value"
    )
    target, event, props = event_handler.serialize().split("_")
    assert target == "uuid"
    assert event == "onKeyPress"
    assert set(props.split(";")) == {"key", "target.value"}


async def test_event_handler_props_to_params_mapping():
    calls = []

    async def handler(key, value):
        calls.append((key, value))

    event_handler = EventHandler("onKeyPress")
    # test you can register multiple handlers
    event_handler.add(handler, "value=target.value")
    event_handler.add(handler, "value=target.value")

    await event_handler({"key": 1, "target.value": 2})
    assert calls == [(1, 2), (1, 2)]


def test_event_handler_variable_arguments_are_illegal():
    eh = EventHandler("event")

    def handler(*args):
        pass

    with pytest.raises(TypeError):
        eh.add(handler)

    def handler(**kwargs):
        pass

    with pytest.raises(TypeError):
        eh.add(handler)
