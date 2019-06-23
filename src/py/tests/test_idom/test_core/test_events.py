import idom
from idom.core.events import EventHandler


def test_simple_events_object():
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
    assert EventHandler(target_id="uuid").serialize() == {
        "target": "uuid",
        "stopPropagation": False,
        "preventDefault": False,
    }
    assert EventHandler(target_id="uuid", prevent_default=True).serialize() == {
        "target": "uuid",
        "stopPropagation": False,
        "preventDefault": True,
    }
    assert EventHandler(target_id="uuid", stop_propagation=True).serialize() == {
        "target": "uuid",
        "stopPropagation": True,
        "preventDefault": False,
    }


async def test_multiple_callbacks_per_event_handler():
    calls = []

    event_handler = EventHandler()

    @event_handler.add
    async def callback_1(event):
        calls.append(1)

    @event_handler.add
    async def callback_2(event):
        calls.append(2)

    await event_handler({})

    assert calls == [1, 2]
