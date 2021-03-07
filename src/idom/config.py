from pathlib import Path

from ._option import Option

IDOM_DEBUG_MODE = Option(
    "IDOM_DEBUG_MODE",
    default=False,
    allow_changes=False,
    from_string=lambda x: bool(int(x)),
)
"""Turn on/off debug mode"""

IDOM_CLIENT_BUILD_DIR = Option(
    "IDOM_CLIENT_BUILD_DIR",
    default=Path(__file__).parent / "client" / "build",
    from_string=Path,
)
"""The location IDOM will use for its client application"""

IDOM_CLIENT_WEB_MODULE_BASE_URL = Option(
    "IDOM_CLIENT_WEB_MODULE_BASE_URL",
    default="./_snowpack/pkg",
)
"""The base URL where all user-installed web modules reside"""
