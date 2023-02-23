import pytest

from reactpy import config
from reactpy._option import Option


@pytest.fixture(autouse=True)
def reset_options():
    options = [value for value in config.__dict__.values() if isinstance(value, Option)]

    should_unset = object()
    original_values = []
    for opt in options:
        original_values.append(opt.current if opt.is_set() else should_unset)

    yield

    for opt, val in zip(options, original_values):
        if val is should_unset:
            if opt.is_set():
                opt.unset()
        else:
            opt.current = val


def test_reactpy_debug_mode_toggle():
    # just check that nothing breaks
    config.REACTPY_DEBUG_MODE.current = True
    config.REACTPY_DEBUG_MODE.current = False
