import pytest

import idom
from idom.core.utils import AsyncOpenClose, must_by_open


async def test_async_open_close():
    open_method_triggered = idom.Var(False)
    close_method_triggered = idom.Var(False)

    class MyResource(AsyncOpenClose):
        async def open(self):
            await super().open()
            open_method_triggered.set(True)

        async def close(self):
            await super().close()
            close_method_triggered.set(True)

    resource = MyResource()

    assert not open_method_triggered.value
    assert not close_method_triggered.value
    assert not resource.opened
    assert not resource.closed

    async with resource:
        assert open_method_triggered.value
        assert not close_method_triggered.value
        assert resource.opened
        assert not resource.closed

    assert close_method_triggered.value
    assert not resource.opened
    assert resource.closed

    with pytest.raises(RuntimeError, match="is closed"):
        await resource.open()


async def test_must_by_open():
    class MyResource(AsyncOpenClose):
        @must_by_open()
        async def coro_must_by_open_when_called(self):
            pass

        @must_by_open()
        def method_must_by_open_when_called(self):
            pass

    resource = MyResource()

    with pytest.raises(RuntimeError, match="is not open"):
        await resource.coro_must_by_open_when_called()

    with pytest.raises(RuntimeError, match="is not open"):
        resource.method_must_by_open_when_called()

    async with resource:
        await resource.coro_must_by_open_when_called()
        resource.method_must_by_open_when_called()

    with pytest.raises(RuntimeError, match="is closed"):
        await resource.coro_must_by_open_when_called()

    with pytest.raises(RuntimeError, match="is closed"):
        resource.method_must_by_open_when_called()
