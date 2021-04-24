import asyncio
from typing import Any, Sequence

import pytest

import idom
from idom.core.dispatcher import (
    create_shared_view_dispatcher,
    dispatch_single_view,
    ensure_shared_view_dispatcher_future,
)
from idom.core.layout import Layout, LayoutEvent, LayoutUpdate
from idom.testing import StaticEventHandler


EVENT_NAME = "onEvent"
EVENT_HANDLER = StaticEventHandler()


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
            raise asyncio.CancelledError()

    async def recv():
        await sem.acquire()
        try:
            return events_to_inject.pop(0)
        except IndexError:
            # wait forever
            await asyncio.Event().wait()

    return changes, send, recv


def make_events_and_expected_model():
    events = [LayoutEvent(EVENT_HANDLER.target, [])] * 4
    expected_model = {
        "tagName": "div",
        "attributes": {"count": 4},
        "eventHandlers": {
            EVENT_NAME: {
                "target": EVENT_HANDLER.target,
                "preventDefault": False,
                "stopPropagation": False,
            }
        },
    }
    return events, expected_model


def assert_changes_produce_expected_model(
    changes: Sequence[LayoutUpdate],
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
    handler = EVENT_HANDLER.use(lambda: change_count(1))
    return idom.html.div({EVENT_NAME: handler, "count": count})


async def test_dispatch_single_view():
    events, expected_model = make_events_and_expected_model()
    changes, send, recv = make_send_recv_callbacks(events)
    await dispatch_single_view(Layout(Counter()), send, recv)
    assert_changes_produce_expected_model(changes, expected_model)


async def test_create_shared_state_dispatcher():
    events, model = make_events_and_expected_model()
    changes_1, send_1, recv_1 = make_send_recv_callbacks(events)
    changes_2, send_2, recv_2 = make_send_recv_callbacks(events)

    async with create_shared_view_dispatcher(Layout(Counter())) as dispatcher:
        dispatcher(send_1, recv_1)
        dispatcher(send_2, recv_2)

    assert_changes_produce_expected_model(changes_1, model)
    assert_changes_produce_expected_model(changes_2, model)


async def test_ensure_shared_view_dispatcher_future():
    events, model = make_events_and_expected_model()
    changes_1, send_1, recv_1 = make_send_recv_callbacks(events)
    changes_2, send_2, recv_2 = make_send_recv_callbacks(events)

    dispatch_future, dispatch = ensure_shared_view_dispatcher_future(Layout(Counter()))

    await asyncio.gather(
        dispatch(send_1, recv_1),
        dispatch(send_2, recv_2),
        return_exceptions=True,
    )

    # the dispatch future should run forever, until cancelled
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(dispatch_future, timeout=1)

    dispatch_future.cancel()
    await asyncio.gather(dispatch_future, return_exceptions=True)

    assert_changes_produce_expected_model(changes_1, model)
    assert_changes_produce_expected_model(changes_2, model)
