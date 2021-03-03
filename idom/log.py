import logging
import sys
from logging.config import dictConfig

from ._options import IDOM_DEBUG_MODE

root_logger = logging.getLogger("idom")


LOGGING_CONFIG_DEFAULTS = {
    "version": 1,
    "disable_existing_loggers": False,
    "loggers": {
        "idom": {
            "level": "DEBUG" if IDOM_DEBUG_MODE else "INFO",
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
            "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            "datefmt": r"%Y-%m-%dT%H:%M:%S%z",
            "class": "logging.Formatter",
        }
    },
}


dictConfig(LOGGING_CONFIG_DEFAULTS)
