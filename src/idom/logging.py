import logging
import sys
from logging.config import dictConfig

from .config import IDOM_DEBUG_MODE


dictConfig(
    {
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
                "format": "%(asctime)s | %(log_color)s%(levelname)s%(reset)s | %(message)s",
                "datefmt": r"%Y-%m-%dT%H:%M:%S%z",
                "class": "colorlog.ColoredFormatter",
            }
        },
    }
)


ROOT_LOGGER = logging.getLogger("idom")
"""IDOM's root logger instance"""


if IDOM_DEBUG_MODE.current:
    ROOT_LOGGER.debug("IDOM is in debug mode")
