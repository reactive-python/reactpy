import asyncio
from tests.general_utils import assert_same_items

import pytest
from anyio import ExceptionGroup

import idom
from idom.core.layout import Layout, LayoutEvent
from idom.core.dispatcher import (
    SharedViewDispatcher,
    AbstractDispatcher,
    SingleViewDispatcher,
)


async def test_shared_state_dispatcher():
    done = asyncio.Event()
    changes_1 = []
    changes_2 = []
    target_id = "an-event"

    events_to_inject = [LayoutEvent(target=target_id, data=[])] * 4

    async def send_1(patch):
        changes_1.append(patch.changes)

    async def recv_1():
        await asyncio.sleep(0)
        try:
            return events_to_inject.pop(0)
        except IndexError:
            done.set()
            raise asyncio.CancelledError()

    async def send_2(patch):
        changes_2.append(patch.changes)

    async def recv_2():
        await done.wait()
        raise asyncio.CancelledError()

    @idom.element
    def Clickable():
        count, set_count = idom.hooks.use_state(0)

        @idom.event(target_id=target_id)
        async def an_event():
            set_count(count + 1)

        return idom.html.div({"anEvent": an_event, "count": count})

    async with SharedViewDispatcher(Layout(Clickable())) as dispatcher:
        await dispatcher.run(send_1, recv_1, "1")
        await dispatcher.run(send_2, recv_2, "2")

    expected_changes = [
        [
            {
                "op": "add",
                "path": "/eventHandlers",
                "value": {
                    "anEvent": {
                        "target": "an-event",
                        "preventDefault": False,
                        "stopPropagation": False,
                    }
                },
            },
            {"op": "add", "path": "/attributes", "value": {"count": 0}},
            {"op": "add", "path": "/tagName", "value": "div"},
        ],
        [{"op": "replace", "path": "/attributes/count", "value": 1}],
        [{"op": "replace", "path": "/attributes/count", "value": 2}],
        [{"op": "replace", "path": "/attributes/count", "value": 3}],
    ]

    for c_2, expected_c in zip(changes_2, expected_changes):
        assert_same_items(c_2, expected_c)

    assert changes_1 == changes_2


async def test_dispatcher_run_does_not_supress_non_cancel_errors():
    class DispatcherWithBug(AbstractDispatcher):
        async def _outgoing(self, layout, context):
            raise ValueError("this is a bug")

        async def _incoming(self, layout, context, message):
            raise ValueError("this is a bug")

    @idom.element
    def AnyElement():
        return idom.html.div()

    async def send(data):
        pass

    async def recv():
        return {}

    with pytest.raises(ExceptionGroup, match="this is a bug"):
        async with DispatcherWithBug(idom.Layout(AnyElement())) as dispatcher:
            await dispatcher.run(send, recv, None)


async def test_dispatcher_run_does_not_supress_errors():
    class DispatcherWithBug(AbstractDispatcher):
        async def _outgoing(self, layout, context):
            raise ValueError("this is a bug")

        async def _incoming(self, layout, context, message):
            raise ValueError("this is a bug")

    @idom.element
    def AnyElement():
        return idom.html.div()

    async def send(data):
        pass

    async def recv():
        return {}

    with pytest.raises(ExceptionGroup, match="this is a bug"):
        async with DispatcherWithBug(idom.Layout(AnyElement())) as dispatcher:
            await dispatcher.run(send, recv, None)


async def test_dispatcher_start_stop():
    cancelled_recv = False
    cancelled_send = False

    async def send(patch):
        nonlocal cancelled_send
        try:
            await asyncio.sleep(100)
        except asyncio.CancelledError:
            cancelled_send = True
            raise
        else:
            assert False, "this should never be reached"

    async def recv():
        nonlocal cancelled_recv
        try:
            await asyncio.sleep(100)
        except asyncio.CancelledError:
            cancelled_recv = True
            raise
        else:
            assert False, "this should never be reached"

    @idom.element
    def AnElement():
        return idom.html.div()

    dispatcher = SingleViewDispatcher(Layout(AnElement()))

    await dispatcher.start()

    await dispatcher.run(send, recv, None)

    # let it run until it hits the sleeping recv/send calls
    for i in range(10):
        await asyncio.sleep(0)

    await dispatcher.stop()

    assert cancelled_recv
    assert cancelled_send
