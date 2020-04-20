import logging
import inspect

from loguru import logger
import pytest
from _pytest.logging import caplog as _caplog  # noqa


def pytest_collection_modifyitems(items):
    for item in items:
        if isinstance(item, pytest.Function):
            if inspect.iscoroutinefunction(item.function):
                item.add_marker(pytest.mark.asyncio)


def pytest_addoption(parser):
    parser.addoption(
        "--headless",
        action="store_true",
        help="Whether to run browser tests in headless mode.",
    )


@pytest.fixture
def caplog(_caplog):
    class PropogateHandler(logging.Handler):
        def emit(self, record):
            logging.getLogger(record.name).handle(record)

    handler_id = logger.add(PropogateHandler(), format="{message}")
    yield _caplog
    logger.remove(handler_id)
