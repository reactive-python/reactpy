import asyncio
from collections.abc import Sequence
from typing import Any

from jsonpointer import set_pointer

import reactpy
from reactpy.core.layout import Layout
from reactpy.core.serve import serve_layout
from reactpy.core.types import LayoutUpdateMessage
from reactpy.testing import StaticEventHandler
from tests.tooling.common import event_message

EVENT_NAME = "on_event"
STATIC_EVENT_HANDLER = StaticEventHandler()


def make_send_recv_callbacks(events_to_inject):
    changes = []

    # We need a semaphore here to simulate receiving an event after each update is sent.
    # The effect is that the send() and recv() callbacks trade off control. If we did
    # not do this, it would easy to determine when to halt because, while we might have
    # received all the events, they might not have been sent since the two callbacks are
    # executed in separate loops.
    sem = asyncio.Semaphore(0)

    async def send(patch):
        changes.append(patch)
        sem.release()
        if not events_to_inject:
            raise reactpy.Stop()

    async def recv():
        await sem.acquire()
        try:
            return events_to_inject.pop(0)
        except IndexError:
            # wait forever
            await asyncio.Event().wait()

    return changes, send, recv


def make_events_and_expected_model():
    events = [event_message(STATIC_EVENT_HANDLER.target)] * 4
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
        if update["path"]:
            model_from_changes = set_pointer(
                model_from_changes, update["path"], update["model"]
            )
        else:
            model_from_changes.update(update["model"])
    assert model_from_changes == expected_model


@reactpy.component
def Counter():
    count, change_count = reactpy.hooks.use_reducer(
        (lambda old_count, diff: old_count + diff),
        initial_value=0,
    )
    handler = STATIC_EVENT_HANDLER.use(lambda: change_count(1))
    return reactpy.html.div({EVENT_NAME: handler, "count": count})


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

    @reactpy.component
    def ComponentWithTwoEventHandlers():
        @blocked_handler.use
        async def block_forever():
            will_block.set()
            await block_and_never_set.wait()

        @non_blocked_handler.use
        async def handle_event():
            second_event_did_execute.set()

        return reactpy.html.div(
            reactpy.html.button({"on_click": block_forever}),
            reactpy.html.button({"on_click": handle_event}),
        )

    send_queue = asyncio.Queue()
    recv_queue = asyncio.Queue()

    task = asyncio.create_task(
        serve_layout(
            reactpy.Layout(ComponentWithTwoEventHandlers()),
            send_queue.put,
            recv_queue.get,
        )
    )

    await recv_queue.put(event_message(blocked_handler.target))
    await will_block.wait()

    await recv_queue.put(event_message(non_blocked_handler.target))
    await second_event_did_execute.wait()

    task.cancel()
