import sys
from unittest import mock

import pytest


def test_asgi_import_error():
    # Remove the module if it's already loaded so we can trigger the import logic
    if "reactpy.executors.asgi" in sys.modules:
        del sys.modules["reactpy.executors.asgi"]

    # Mock one of the required modules to be missing (None in sys.modules causes ModuleNotFoundError)
    with mock.patch.dict(sys.modules, {"reactpy.executors.asgi.middleware": None}):
        with pytest.raises(
            ModuleNotFoundError,
            match=r"ASGI executors require the 'reactpy\[asgi\]' extra to be installed",
        ):
            import reactpy.executors.asgi  # noqa: F401

    # Clean up
    if "reactpy.executors.asgi" in sys.modules:
        del sys.modules["reactpy.executors.asgi"]
