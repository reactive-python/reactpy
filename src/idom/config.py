"""
Configuration Options
=====================

IDOM provides a series of configuration options that can be set using environment
variables or, for those which allow it, a programatic interface.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

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
performance but can be used to catch bugs. Additionally, the default log level for IDOM
is set to ``DEBUG``.
"""

# Because these web modules will be linked dynamically at runtime this can be temporary
_DEFAULT_WEB_MODULES_DIR = TemporaryDirectory()

IDOM_WED_MODULES_DIR = _Option(
    "IDOM_WED_MODULES_DIR",
    default=Path(_DEFAULT_WEB_MODULES_DIR.name),
    validator=Path,
)
"""The location IDOM will use to store its client application

This directory **MUST** be treated as a black box. Downstream applications **MUST NOT**
assume anything about the structure of this directory see :mod:`idom.web.module` for a
set of publically available APIs for working with the client.
"""

IDOM_FEATURE_INDEX_AS_DEFAULT_KEY = _Option(
    "IDOM_FEATURE_INDEX_AS_DEFAULT_KEY",
    default=False,
    mutable=False,
    validator=lambda x: bool(int(x)),
)
"""Use the index of elements/components amongst their siblings as the default key.

In a future release this flag's default value will be set to true, and after that, this
flag will be removed entirely and the indices will always be the default key.

For more information on changes to this feature flag see: https://github.com/idom-team/idom/issues/351
"""
