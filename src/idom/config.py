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
"""The location IDOM will use to store its client application"""

IDOM_CLIENT_WEB_MODULE_BASE_URL = _option.Option(
    "IDOM_CLIENT_WEB_MODULE_BASE_URL",
    default=".",
    validator=lambda x: cast(str, x[:-1] if x.endswith("/") else x),
)
"""The base URL where all user-installed web modules reside"""
