import logging
import sys
from logging.config import dictConfig

from reactpy.config import REACTPY_DEBUG_MODE

dictConfig(
    {
        "version": 1,
        "disable_existing_loggers": False,
        "loggers": {
            "reactpy": {"handlers": ["console"]},
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


ROOT_LOGGER = logging.getLogger("reactpy")
"""ReactPy's root logger instance"""


@REACTPY_DEBUG_MODE.subscribe
def _set_debug_level(debug: bool) -> None:
    if debug:
        ROOT_LOGGER.setLevel("DEBUG")
        ROOT_LOGGER.debug("ReactPy is in debug mode")
    else:
        ROOT_LOGGER.setLevel("INFO")
