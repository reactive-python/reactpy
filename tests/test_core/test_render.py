import asyncio

import pytest
from anyio.exceptions import ExceptionGroup

import idom
from idom.core.layout import Layout, LayoutEvent
from idom.core.render import SharedStateRenderer, AbstractRenderer


async def test_shared_state_renderer():
    done = asyncio.Event()
    data_sent_1 = asyncio.Queue()
    data_sent_2 = []

    async def send_1(data):
        await data_sent_1.put(data)

    async def recv_1():
        sent = await data_sent_1.get()

        element_id = sent["root"]
        element_data = sent["new"][element_id]
        if element_data["attributes"]["count"] == 4:
            done.set()
            raise asyncio.CancelledError()

        return LayoutEvent(target="an-event", data=[])

    async def send_2(data):
        element_id = data["root"]
        element_data = data["new"][element_id]
        data_sent_2.append(element_data["attributes"]["count"])

    async def recv_2():
        await done.wait()
        raise asyncio.CancelledError()

    @idom.element
    async def Clickable(count=0):
        count, set_count = idom.hooks.use_state(count)

        @idom.event(target_id="an-event")
        async def an_event():
            set_count(count + 1)

        return idom.html.div({"anEvent": an_event, "count": count})

    async with SharedStateRenderer(Layout(Clickable())) as renderer:
        await renderer.run(send_1, recv_1, "1")
        await renderer.run(send_2, recv_2, "2")

    assert data_sent_2 == [0, 1, 2, 3, 4]


async def test_renderer_run_does_not_supress_non_stop_rendering_errors():
    class RendererWithBug(AbstractRenderer):
        async def _outgoing(self, layout, context):
            raise ValueError("this is a bug")

        async def _incoming(self, layout, context, message):
            raise ValueError("this is a bug")

    @idom.element
    async def AnyElement():
        return idom.html.div()

    async def send(data):
        pass

    async def recv():
        return {}

    with pytest.raises(ExceptionGroup, match="this is a bug"):
        async with RendererWithBug(idom.Layout(AnyElement())) as renderer:
            await renderer.run(send, recv, None)


async def test_shared_state_renderer_deletes_old_elements():
    sent = []
    target_id = "some-id"

    async def send(data):
        if len(sent) == 2:
            raise asyncio.CancelledError()
        sent.append(data)

    async def recv():
        # If we don't sleep here recv callback will clog the event loop.
        # In practice this isn't a problem because you'll usually be awaiting
        # something here that would take the place of sleep()
        await asyncio.sleep(0)
        return LayoutEvent(target_id, [])

    @idom.element
    async def Outer():
        update = idom.hooks.dispatch_hook().create_update_callback()

        @idom.event(target_id=target_id)
        async def an_event():
            update()

        return idom.html.div({"onEvent": an_event}, Inner())

    @idom.element
    async def Inner():
        return idom.html.div()

    layout = Layout(Outer())
    async with SharedStateRenderer(layout) as renderer:
        await renderer.run(send, recv, "1")

    root = sent[0]["new"][layout.root]
    first_inner_id = root["children"][0]["data"]
    assert sent[1]["old"] == [first_inner_id]
