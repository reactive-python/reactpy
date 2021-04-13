# dialect=pytest

from contextlib import contextmanager


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


def assert_same_items(left, right):
    """Check that two unordered sequences are equal (only works if reprs are equal)"""
    sorted_left = list(sorted(left, key=repr))
    sorted_right = list(sorted(right, key=repr))
    assert sorted_left == sorted_right
