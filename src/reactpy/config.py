"""
ReactPy provides a series of configuration options that can be set using environment
variables or, for those which allow it, a programmatic interface.
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from reactpy._option import Option

TRUE_VALUES = {"true", "1"}
FALSE_VALUES = {"false", "0"}


def boolean(value: str | bool | int) -> bool:
    if isinstance(value, bool):
        return value
    elif isinstance(value, int):
        return bool(value)
    elif not isinstance(value, str):
        raise TypeError(f"Expected str or bool, got {type(value).__name__}")

    if value.lower() in TRUE_VALUES:
        return True
    elif value.lower() in FALSE_VALUES:
        return False
    else:
        raise ValueError(
            f"Invalid boolean value {value!r} - expected "
            f"one of {list(TRUE_VALUES | FALSE_VALUES)}"
        )


REACTPY_DEBUG = Option("REACTPY_DEBUG", default=False, validator=boolean, mutable=True)
"""Get extra logs and validation checks at the cost of performance.

This will enable the following:

- :data:`REACTPY_CHECK_VDOM_SPEC`
- :data:`REACTPY_CHECK_JSON_ATTRS`
"""

REACTPY_CHECK_VDOM_SPEC = Option(
    "REACTPY_CHECK_VDOM_SPEC", parent=REACTPY_DEBUG, validator=boolean
)
"""Checks which ensure VDOM is rendered to spec

For more info on the VDOM spec, see here: :ref:`VDOM JSON Schema`
"""

REACTPY_CHECK_JSON_ATTRS = Option(
    "REACTPY_CHECK_JSON_ATTRS", parent=REACTPY_DEBUG, validator=boolean
)
"""Checks that all VDOM attributes are JSON serializable

The VDOM spec is not able to enforce this on its own since attributes could anything.
"""

# Because these web modules will be linked dynamically at runtime this can be temporary.
# Assigning to a variable here ensures that the directory is not deleted until the end
# of the program.
_DEFAULT_WEB_MODULES_DIR = TemporaryDirectory()

REACTPY_WEB_MODULES_DIR = Option(
    "REACTPY_WEB_MODULES_DIR",
    default=Path(_DEFAULT_WEB_MODULES_DIR.name),
    validator=Path,
)
"""The location ReactPy will use to store its client application

This directory **MUST** be treated as a black box. Downstream applications **MUST NOT**
assume anything about the structure of this directory see :mod:`reactpy.web.module` for a
set of publicly available APIs for working with the client.
"""

REACTPY_TESTS_DEFAULT_TIMEOUT = Option(
    "REACTPY_TESTS_DEFAULT_TIMEOUT",
    15.0,
    mutable=False,
    validator=float,
)
"""A default timeout for testing utilities in ReactPy"""

REACTPY_ASYNC_RENDERING = Option(
    "REACTPY_ASYNC_RENDERING",
    default=True,
    mutable=True,
    validator=boolean,
)
"""Whether to render components asynchronously."""

REACTPY_RECONNECT_INTERVAL = Option(
    "REACTPY_RECONNECT_INTERVAL",
    default=750,
    mutable=True,
    validator=int,
)
"""The interval in milliseconds between reconnection attempts for the websocket server"""

REACTPY_RECONNECT_MAX_INTERVAL = Option(
    "REACTPY_RECONNECT_MAX_INTERVAL",
    default=60000,
    mutable=True,
    validator=int,
)
"""The maximum interval in milliseconds between reconnection attempts for the websocket server"""

REACTPY_RECONNECT_MAX_RETRIES = Option(
    "REACTPY_RECONNECT_MAX_RETRIES",
    default=150,
    mutable=True,
    validator=int,
)
"""The maximum number of reconnection attempts for the websocket server"""

REACTPY_RECONNECT_BACKOFF_MULTIPLIER = Option(
    "REACTPY_RECONNECT_BACKOFF_MULTIPLIER",
    default=1.25,
    mutable=True,
    validator=float,
)
"""The multiplier for exponential backoff between reconnection attempts for the websocket server"""

REACTPY_PATH_PREFIX = Option(
    "REACTPY_PATH_PREFIX",
    default="/reactpy/",
    mutable=True,
    validator=str,
)
"""The prefix for all ReactPy routes"""
