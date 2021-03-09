from pathlib import Path

from . import _option


IDOM_DEBUG_MODE = _option.Option(
    "IDOM_DEBUG_MODE",
    default=False,
    allow_changes=False,
    validator=lambda x: bool(int(x)),
)
"""Turn on/off debug mode"""

IDOM_CLIENT_BUILD_DIR = _option.Option(
    "IDOM_CLIENT_BUILD_DIR",
    default=Path(__file__).parent / "client" / "build",
    validator=Path,
)
"""The location IDOM will use for its client application"""

IDOM_CLIENT_WEB_MODULE_BASE_URL = _option.Option(
    "IDOM_CLIENT_WEB_MODULE_BASE_URL",
    default=".",
    validator=lambda x: str(x).rstrip("/"),
)
"""The base URL where all user-installed web modules reside"""
