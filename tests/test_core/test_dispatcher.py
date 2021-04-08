import asyncio

import pytest
from anyio import ExceptionGroup

import idom
from idom.core.dispatcher import (
    AbstractDispatcher,
    SharedViewDispatcher,
    SingleViewDispatcher,
)
from idom.core.layout import Layout, LayoutEvent
from tests.general_utils import assert_same_items


async def test_shared_state_dispatcher():
    done = asyncio.Event()
    changes_1 = []
    changes_2 = []
    event_name = "onEvent"
    target_id = f"/{event_name}"

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

    @idom.component
    def Clickable():
        count, set_count = idom.hooks.use_state(0)
        return idom.html.div({event_name: lambda: set_count(count + 1), "count": count})

    async with SharedViewDispatcher(Layout(Clickable())) as dispatcher:
        await dispatcher.run(send_1, recv_1, "1")
        await dispatcher.run(send_2, recv_2, "2")

    expected_changes = [
        [
            {
                "op": "add",
                "path": "/eventHandlers",
                "value": {
                    event_name: {
                        "target": target_id,
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

    @idom.component
    def AnyComponent():
        return idom.html.div()

    async def send(data):
        pass

    async def recv():
        return {}

    with pytest.raises(ExceptionGroup, match="this is a bug"):
        async with DispatcherWithBug(idom.Layout(AnyComponent())) as dispatcher:
            await dispatcher.run(send, recv, None)


async def test_dispatcher_run_does_not_supress_errors():
    class DispatcherWithBug(AbstractDispatcher):
        async def _outgoing(self, layout, context):
            raise ValueError("this is a bug")

        async def _incoming(self, layout, context, message):
            raise ValueError("this is a bug")

    @idom.component
    def AnyComponent():
        return idom.html.div()

    async def send(data):
        pass

    async def recv():
        return {}

    with pytest.raises(ExceptionGroup, match="this is a bug"):
        async with DispatcherWithBug(idom.Layout(AnyComponent())) as dispatcher:
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

    @idom.component
    def AnyComponent():
        return idom.html.div()

    dispatcher = SingleViewDispatcher(Layout(AnyComponent()))

    await dispatcher.start()

    await dispatcher.run(send, recv, None)

    # let it run until it hits the sleeping recv/send calls
    for i in range(10):
        await asyncio.sleep(0)

    await dispatcher.stop()

    assert cancelled_recv
    assert cancelled_send
