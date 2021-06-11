"""
Logging
=======
"""

import logging
import sys
from logging.config import dictConfig
from typing import Any

from .config import IDOM_DEBUG_MODE


root_logger = logging.getLogger("idom")


def logging_config_defaults() -> Any:
    """Get default logging configuration"""
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "loggers": {
            "idom": {
                "level": "DEBUG" if IDOM_DEBUG_MODE.current else "INFO",
                "handlers": ["console"],
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "generic",
                "stream": sys.stdout,
            }
        },
        "formatters": {
            "generic": {
                "format": "%(asctime)s | %(levelname)s | %(message)s",
                "datefmt": r"%Y-%m-%dT%H:%M:%S%z",
                "class": "logging.Formatter",
            }
        },
    }


dictConfig(logging_config_defaults())


if IDOM_DEBUG_MODE.current:
    root_logger.debug("IDOM is in debug mode")
