"""
IDOM provides a series of configuration options that can be set using environment
variables or, for those which allow it, a programatic interface.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

from ._option import DeprecatedOption as _DeprecatedOption
from ._option import Option as _Option


IDOM_DEBUG_MODE = _Option(
    "IDOM_DEBUG_MODE",
    default=False,
    mutable=False,
    validator=lambda x: bool(int(x)),
)
"""This immutable option turns on/off debug mode

The string values ``1`` and ``0`` are mapped to ``True`` and ``False`` respectively.

When debug is on, extra validation measures are applied that negatively impact
performance but can be used to catch bugs during development. Additionally, the default
log level for IDOM is set to ``DEBUG``.
"""

IDOM_CHECK_VDOM_SPEC = _Option(
    "IDOM_CHECK_VDOM_SPEC",
    default=IDOM_DEBUG_MODE.current,
    mutable=False,
    validator=lambda x: bool(int(x)),
)
"""This immutable option turns on/off checks which ensure VDOM is rendered to spec

The string values ``1`` and ``0`` are mapped to ``True`` and ``False`` respectively.

By default this check is off. When ``IDOM_DEBUG_MODE=1`` this will be turned on but can
be manually disablled by setting ``IDOM_CHECK_VDOM_SPEC=0`` in addition.

For more info on the VDOM spec, see here: :ref:`VDOM JSON Schema`
"""

# Because these web modules will be linked dynamically at runtime this can be temporary
_DEFAULT_WEB_MODULES_DIR = TemporaryDirectory()

IDOM_WEB_MODULES_DIR = _Option(
    "IDOM_WEB_MODULES_DIR",
    default=Path(_DEFAULT_WEB_MODULES_DIR.name),
    validator=Path,
)
"""The location IDOM will use to store its client application

This directory **MUST** be treated as a black box. Downstream applications **MUST NOT**
assume anything about the structure of this directory see :mod:`idom.web.module` for a
set of publically available APIs for working with the client.
"""

IDOM_WED_MODULES_DIR: _Option[Path] = _DeprecatedOption(
    new_opt=IDOM_WEB_MODULES_DIR,
    name="IDOM_WED_MODULES_DIR",
)
"""This has been renamed to :data:`IDOM_WEB_MODULES_DIR`"""

IDOM_FEATURE_INDEX_AS_DEFAULT_KEY = _Option(
    "IDOM_FEATURE_INDEX_AS_DEFAULT_KEY",
    default=True,
    mutable=False,
    validator=lambda x: bool(int(x)),
)
"""Use the index of elements/components amongst their siblings as the default key.

The flag's default value is set to true. To return to legacy behavior set
``IDOM_FEATURE_INDEX_AS_DEFAULT_KEY=0``. In a future release, this flag will be removed
entirely and the indices will always be the default key.

For more information on changes to this feature flag see:
https://github.com/idom-team/idom/issues/351
"""

IDOM_TESTING_DEFAULT_TIMEOUT = _Option(
    "IDOM_TESTING_DEFAULT_TIMEOUT",
    5.0,
    mutable=False,
    validator=float,
)
"""A default timeout for testing utilities in IDOM"""
