import pytest

from idom.core.utils import HasAsyncResources, async_resource


async def test_simple_async_resource():
    class MyResources(HasAsyncResources):

        before = False
        after = False

        @async_resource
        async def x(self):
            self.before = True
            yield 1
            self.after = True

    my_resources = MyResources()

    with pytest.raises(RuntimeError, match="is not open"):
        my_resources.x

    assert not my_resources.before
    async with my_resources:
        assert my_resources.before
        assert my_resources.x == 1
        assert not my_resources.after
    assert my_resources.after

    with pytest.raises(RuntimeError, match="is not open"):
        my_resources.x


async def test_resource_opens_only_once():
    class MyResources(HasAsyncResources):
        pass

    with pytest.raises(RuntimeError, match="is already open"):
        async with MyResources() as rsrc:
            async with rsrc:
                pass


async def test_unexpected_resource_close_before_open():
    class MyResources(HasAsyncResources):
        @async_resource
        async def x(self):
            yield 1

    with pytest.raises(RuntimeError, match="is not open"):
        rsrc = MyResources()
        await MyResources.x.close(rsrc, None, None, None)
