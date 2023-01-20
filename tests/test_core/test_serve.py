import asyncio
from typing import Any, Sequence

import idom
from idom.core.layout import Layout, LayoutEventMessage, LayoutUpdateMessage
from idom.core.serve import LayoutUpdateMessage, serve_layout
from idom.testing import StaticEventHandler


EVENT_NAME = "onEvent"
STATIC_EVENT_HANDLER = StaticEventHandler()


def test_vdom_json_patch_create_from_apply_to():
    update = LayoutUpdateMessage("", {"a": 1, "b": [1]}, {"a": 2, "b": [1, 2]})
    patch = LayoutUpdateMessage.create_from(update)
    result = patch.apply_to({"a": 1, "b": [1]})
    assert result == {"a": 2, "b": [1, 2]}


def make_send_recv_callbacks(events_to_inject):
    changes = []

    # We need a semaphor here to simulate recieving an event after each update is sent.
    # The effect is that the send() and recv() callbacks trade off control. If we did
    # not do this, it would easy to determine when to halt because, while we might have
    # received all the events, they might not have been sent since the two callbacks are
    # executed in separate loops.
    sem = asyncio.Semaphore(0)

    async def send(patch):
        changes.append(patch)
        sem.release()
        if not events_to_inject:
            raise idom.Stop()

    async def recv():
        await sem.acquire()
        try:
            return events_to_inject.pop(0)
        except IndexError:
            # wait forever
            await asyncio.Event().wait()

    return changes, send, recv


def make_events_and_expected_model():
    events = [LayoutEventMessage(STATIC_EVENT_HANDLER.target, [])] * 4
    expected_model = {
        "tagName": "",
        "children": [
            {
                "tagName": "div",
                "attributes": {"count": 4},
                "eventHandlers": {
                    EVENT_NAME: {
                        "target": STATIC_EVENT_HANDLER.target,
                        "preventDefault": False,
                        "stopPropagation": False,
                    }
                },
            }
        ],
    }
    return events, expected_model


def assert_changes_produce_expected_model(
    changes: Sequence[LayoutUpdateMessage],
    expected_model: Any,
) -> None:
    model_from_changes = {}
    for update in changes:
        model_from_changes = update.apply_to(model_from_changes)
    assert model_from_changes == expected_model


@idom.component
def Counter():
    count, change_count = idom.hooks.use_reducer(
        (lambda old_count, diff: old_count + diff),
        initial_value=0,
    )
    handler = STATIC_EVENT_HANDLER.use(lambda: change_count(1))
    return idom.html.div({EVENT_NAME: handler, "count": count})


async def test_dispatch():
    events, expected_model = make_events_and_expected_model()
    changes, send, recv = make_send_recv_callbacks(events)
    await asyncio.wait_for(serve_layout(Layout(Counter()), send, recv), 1)
    assert_changes_produce_expected_model(changes, expected_model)


async def test_dispatcher_handles_more_than_one_event_at_a_time():
    block_and_never_set = asyncio.Event()
    will_block = asyncio.Event()
    second_event_did_execute = asyncio.Event()

    blocked_handler = StaticEventHandler()
    non_blocked_handler = StaticEventHandler()

    @idom.component
    def ComponentWithTwoEventHandlers():
        @blocked_handler.use
        async def block_forever():
            will_block.set()
            await block_and_never_set.wait()

        @non_blocked_handler.use
        async def handle_event():
            second_event_did_execute.set()

        return idom.html.div(
            idom.html.button({"onClick": block_forever}),
            idom.html.button({"onClick": handle_event}),
        )

    send_queue = asyncio.Queue()
    recv_queue = asyncio.Queue()

    asyncio.ensure_future(
        serve_layout(
            idom.Layout(ComponentWithTwoEventHandlers()),
            send_queue.put,
            recv_queue.get,
        )
    )

    await recv_queue.put(LayoutEventMessage(blocked_handler.target, []))
    await will_block.wait()

    await recv_queue.put(LayoutEventMessage(non_blocked_handler.target, []))
    await second_event_did_execute.wait()
