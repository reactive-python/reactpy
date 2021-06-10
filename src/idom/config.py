"""
Configuration Options
=====================

IDOM provides a series of configuration options that can be set using environment
variables or, for those which allow it, a programatic interface.
"""

import shutil
from pathlib import Path
from typing import Any, List

from appdirs import user_data_dir

import idom

from ._option import ALL_OPTIONS as _ALL_OPTIONS
from ._option import Option as _Option


def all_options() -> List[_Option[Any]]:
    """Get a list of all options"""
    return list(_ALL_OPTIONS)


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

IDOM_CLIENT_BUILD_DIR = _Option(
    "IDOM_CLIENT_BUILD_DIR",
    default=Path(user_data_dir(idom.__name__, idom.__author__)) / "client",
    validator=Path,
)
"""The location IDOM will use to store its client application

This directory **MUST** be treated as a black box. Downstream applications **MUST NOT**
assume anything about the structure of this directory see :mod:`idom.client.manage` for
a set of publically available APIs for working with the client.
"""

# TODO: remove this in 0.30.0
_DEPRECATED_BUILD_DIR = Path(__file__).parent / "client" / "build"
if _DEPRECATED_BUILD_DIR.exists():  # pragma: no cover
    shutil.rmtree(_DEPRECATED_BUILD_DIR)

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
