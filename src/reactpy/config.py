"""
ReactPy provides a series of configuration options that can be set using environment
variables or, for those which allow it, a programatic interface.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

from ._option import Option as _Option


REACTPY_DEBUG_MODE = _Option(
    "REACTPY_DEBUG_MODE",
    default=False,
    validator=lambda x: bool(int(x)),
)
"""This immutable option turns on/off debug mode

The string values ``1`` and ``0`` are mapped to ``True`` and ``False`` respectively.

When debug is on, extra validation measures are applied that negatively impact
performance but can be used to catch bugs during development. Additionally, the default
log level for ReactPy is set to ``DEBUG``.
"""

REACTPY_CHECK_VDOM_SPEC = _Option(
    "REACTPY_CHECK_VDOM_SPEC",
    default=REACTPY_DEBUG_MODE,
    validator=lambda x: bool(int(x)),
)
"""This immutable option turns on/off checks which ensure VDOM is rendered to spec

The string values ``1`` and ``0`` are mapped to ``True`` and ``False`` respectively.

By default this check is off. When ``REACTPY_DEBUG_MODE=1`` this will be turned on but can
be manually disablled by setting ``REACTPY_CHECK_VDOM_SPEC=0`` in addition.

For more info on the VDOM spec, see here: :ref:`VDOM JSON Schema`
"""

# Because these web modules will be linked dynamically at runtime this can be temporary
_DEFAULT_WEB_MODULES_DIR = TemporaryDirectory()

REACTPY_WEB_MODULES_DIR = _Option(
    "REACTPY_WEB_MODULES_DIR",
    default=Path(_DEFAULT_WEB_MODULES_DIR.name),
    validator=Path,
)
"""The location ReactPy will use to store its client application

This directory **MUST** be treated as a black box. Downstream applications **MUST NOT**
assume anything about the structure of this directory see :mod:`reactpy.web.module` for a
set of publically available APIs for working with the client.
"""

REACTPY_TESTING_DEFAULT_TIMEOUT = _Option(
    "REACTPY_TESTING_DEFAULT_TIMEOUT",
    5.0,
    mutable=False,
    validator=float,
)
"""A default timeout for testing utilities in ReactPy"""
