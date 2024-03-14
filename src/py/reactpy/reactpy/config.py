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


REACTPY_DEBUG_MODE = Option(
    "REACTPY_DEBUG_MODE", default=False, validator=boolean, mutable=True
)
"""Get extra logs and validation checks at the cost of performance.

This will enable the following:

- :data:`REACTPY_CHECK_VDOM_SPEC`
- :data:`REACTPY_CHECK_JSON_ATTRS`
"""

REACTPY_CHECK_VDOM_SPEC = Option("REACTPY_CHECK_VDOM_SPEC", parent=REACTPY_DEBUG_MODE)
"""Checks which ensure VDOM is rendered to spec

For more info on the VDOM spec, see here: :ref:`VDOM JSON Schema`
"""

REACTPY_CHECK_JSON_ATTRS = Option("REACTPY_CHECK_JSON_ATTRS", parent=REACTPY_DEBUG_MODE)
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

REACTPY_TESTING_DEFAULT_TIMEOUT = Option(
    "REACTPY_TESTING_DEFAULT_TIMEOUT",
    5.0,
    mutable=False,
    validator=float,
)
"""A default timeout for testing utilities in ReactPy"""

REACTPY_ASYNC_RENDERING = Option(
    "REACTPY_ASYNC_RENDERING",
    default=False,
    mutable=True,
    validator=boolean,
)
"""Whether to render components asynchronously. This is currently an experimental feature."""
