from functools import wraps
from weakref import ref


import idom


class HookCatcher:
    """Utility for capturing a LifeCycleHook from an element

    Example:
        .. code-block::
            element_hook = HookCatcher()

            @idom.element
            @element_hook.capture
            async def MyElement():
                ...

        After the first render of ``MyElement`` the ``HookCatcher`` will have
        captured the element's ``LifeCycleHook``.
    """

    current: idom.hooks.LifeCycleHook

    def capture(self, render_function):
        """Decorator for capturing a ``LifeCycleHook`` on the first render of an element"""

        # The render function holds a reference to `self` and, via the `LifeCycleHook`,
        # the element. Some tests check whether elements are garbage collected, thus we
        # must use a `ref` here to ensure these checks pass.
        self_ref = ref(self)

        @wraps(render_function)
        async def wrapper(*args, **kwargs):
            self_ref().current = idom.hooks.current_hook()
            return await render_function(*args, **kwargs)

        return wrapper

    def schedule_render(self) -> None:
        """Useful alias of ``HookCatcher.current.schedule_render``"""
        self.current.schedule_render()


def assert_unordered_equal(x, y):
    """Check that two unordered sequences are equal"""

    list_x = list(x)
    list_y = list(y)

    assert len(x) == len(y), f"len({x}) != len({y})"
    assert all(
        # this is not very efficient unfortunately so don't compare anything large
        list_x.count(value) == list_y.count(value)
        for value in list_x
    ), f"{x} != {y}"
