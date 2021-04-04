# dialect=pytest

from contextlib import contextmanager
from functools import wraps
from weakref import ref

import idom


@contextmanager
def patch_slots_object(obj, attr, new_value):
    # we do this since `mock.patch..object attempts to use __dict__
    # which is not necessarilly present on an object with __slots__`
    old_value = getattr(obj, attr)
    setattr(obj, attr, new_value)
    try:
        yield new_value
    finally:
        setattr(obj, attr, old_value)


class HookCatcher:
    """Utility for capturing a LifeCycleHook from a component

    Eleftample:
        .. code-block::
            component_hook = HookCatcher()

            @idom.component
            @component_hook.capture
            def MyComponent():
                ...

        After the first render of ``MyComponent`` the ``HookCatcher`` will have
        captured the component's ``LifeCycleHook``.
    """

    current: idom.hooks.LifeCycleHook

    def capture(self, render_function):
        """Decorator for capturing a ``LifeCycleHook`` on the first render of a component"""

        # The render function holds a reference to `self` and, via the `LifeCycleHook`,
        # the component. Some tests check whether components are garbage collected, thus we
        # must use a `ref` here to ensure these checks pass.
        self_ref = ref(self)

        @wraps(render_function)
        def wrapper(*args, **kwargs):
            self_ref().current = idom.hooks.current_hook()
            return render_function(*args, **kwargs)

        return wrapper

    def schedule_render(self) -> None:
        """Useful alias of ``HookCatcher.current.schedule_render``"""
        self.current.schedule_render()


def assert_same_items(left, right):
    """Check that two unordered sequences are equal (only works if reprs are equal)"""
    sorted_left = list(sorted(left, key=repr))
    sorted_right = list(sorted(right, key=repr))
    assert sorted_left == sorted_right
