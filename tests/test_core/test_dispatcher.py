import asyncio
import sys
from typing import Any, Sequence

import pytest

import idom
from idom.core.layout import Layout, LayoutEvent, LayoutUpdate
from idom.core.serve import (
    VdomJsonPatch,
    _create_shared_view_dispatcher,
    create_shared_view_dispatcher,
    ensure_shared_view_dispatcher_future,
    serve_json_patch,
)
from idom.testing import StaticEventHandler


EVENT_NAME = "onEvent"
STATIC_EVENT_HANDLER = StaticEventHandler()


def test_vdom_json_patch_create_from_apply_to():
    update = LayoutUpdate("", {"a": 1, "b": [1]}, {"a": 2, "b": [1, 2]})
    patch = VdomJsonPatch.create_from(update)
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
    events = [LayoutEvent(STATIC_EVENT_HANDLER.target, [])] * 4
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
    handler = STATIC_EVENT_HANDLER.use(lambda: change_count(1))
    return idom.html.div({EVENT_NAME: handler, "count": count})


async def test_dispatch():
    events, expected_model = make_events_and_expected_model()
    changes, send, recv = make_send_recv_callbacks(events)
    await asyncio.wait_for(serve_json_patch(Layout(Counter()), send, recv), 1)
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


async def test_private_create_shared_view_dispatcher_cleans_up_patch_queues():
    """Report an issue if this test breaks

    Some internals of idom.core.dispatcher may need to be changed in order to make some
    internal state easier to introspect.

    Ideally we would just check if patch queues are getting cleaned up more directly,
    but without having access to that, we use some side effects to try and infer whether
    it happens.
    """

    @idom.component
    def SomeComponent():
        return idom.html.div()

    async def send(patch):
        raise idom.Stop()

    async def recv():
        return LayoutEvent("something", [])

    with idom.Layout(SomeComponent()) as layout:
        dispatch_shared_view, push_patch = await _create_shared_view_dispatcher(layout)

        # Dispatch a view that should exit. After exiting its patch queue should be
        # cleaned up and removed. Since we only dispatched one view there should be
        # no patch queues.
        await dispatch_shared_view(send, recv)  # this should stop immediately

        # We create a patch and check its ref count. We will check this after attempting
        # to push out the change.
        patch = VdomJsonPatch("anything", [])
        patch_ref_count = sys.getrefcount(patch)

        # We push out this change.
        push_patch(patch)

        # Because there should be no patch queues, we expect that the ref count remains
        # the same. If the ref count had increased, then we would know that the patch
        # queue has not been cleaned up and that the patch we just pushed was added to
        # it.
        assert not sys.getrefcount(patch) > patch_ref_count


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
        serve_json_patch(
            idom.Layout(ComponentWithTwoEventHandlers()),
            send_queue.put,
            recv_queue.get,
        )
    )

    await recv_queue.put(LayoutEvent(blocked_handler.target, []))
    await will_block.wait()

    await recv_queue.put(LayoutEvent(non_blocked_handler.target, []))
    await second_event_did_execute.wait()
