from pathlib import Path
from typing import cast

from . import _option


IDOM_DEBUG_MODE = _option.Option(
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

IDOM_CLIENT_BUILD_DIR = _option.Option(
    "IDOM_CLIENT_BUILD_DIR",
    default=Path(__file__).parent / "client" / "build",
    validator=Path,
)
"""The location IDOM will use to store its client application

This directory **MUST** be treated as a black box. Downstream applications **MUST NOT**
assume anything about the structure of this directory see :mod:`idom.client.manage` for
a set of publically available APIs for working with the client.
"""


IDOM_CLIENT_IMPORT_SOURCE_URL = _option.Option(
    "IDOM_CLIENT_IMPORT_SOURCE_URL",
    default="/client",
    validator=lambda x: cast(str, x[:-1] if x.endswith("/") else x),
)
"""The URL to importable modules containing Javascript components

Setting this to an empty string will given the client control over the location of
import sources. Using a relative path (e.g. one starting with ``./``) with locate import
sources relative to a base URL specified by the client. Lastly, an absolute URL
specifies exactly where import sources are located and ignores are client configuration.

Examples:
    Empty String:
        ``CLIENT_SPECIFIED_BASE_URL/my-module.js``
    Relative Path:
        ``CLIENT_SPECIFIED_BASE_URL/RELATIVE_PATH/my-module.js``
    Absolute URL
        ``ABSOLUTE_PATH/my-module.js``
"""
