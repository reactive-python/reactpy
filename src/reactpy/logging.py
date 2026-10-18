import logging
import sys
from logging.config import dictConfig

from reactpy.config import REACTPY_DEBUG

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
        "formatters": {"generic": {"datefmt": r"%Y-%m-%dT%H:%M:%S%z"}},
    }
)


ROOT_LOGGER = logging.getLogger("reactpy")
"""ReactPy's root logger instance"""


@REACTPY_DEBUG.subscribe
def _set_debug_level(debug: bool) -> None:
    if debug:
        ROOT_LOGGER.setLevel("DEBUG")
        ROOT_LOGGER.debug("ReactPy is in debug mode")
    else:
        ROOT_LOGGER.setLevel("INFO")
