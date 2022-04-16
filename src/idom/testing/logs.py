from __future__ import annotations

import logging
import re
from contextlib import contextmanager
from traceback import format_exception
from typing import Any, Iterator, NoReturn

from idom.logging import ROOT_LOGGER


class LogAssertionError(AssertionError):
    """An assertion error raised in relation to log messages."""


@contextmanager
def assert_idom_did_log(
    match_message: str = "",
    error_type: type[Exception] | None = None,
    match_error: str = "",
) -> Iterator[None]:
    """Assert that IDOM produced a log matching the described message or error.

    Args:
        match_message: Must match a logged message.
        error_type: Checks the type of logged exceptions.
        match_error: Must match an error message.
    """
    message_pattern = re.compile(match_message)
    error_pattern = re.compile(match_error)

    with capture_idom_logs() as log_records:
        try:
            yield None
        except Exception:
            raise
        else:
            for record in list(log_records):
                if (
                    # record message matches
                    message_pattern.findall(record.getMessage())
                    # error type matches
                    and (
                        error_type is None
                        or (
                            record.exc_info is not None
                            and record.exc_info[0] is not None
                            and issubclass(record.exc_info[0], error_type)
                        )
                    )
                    # error message pattern matches
                    and (
                        not match_error
                        or (
                            record.exc_info is not None
                            and error_pattern.findall(
                                "".join(format_exception(*record.exc_info))
                            )
                        )
                    )
                ):
                    break
            else:  # pragma: no cover
                _raise_log_message_error(
                    "Could not find a log record matching the given",
                    match_message,
                    error_type,
                    match_error,
                )


@contextmanager
def assert_idom_did_not_log(
    match_message: str = "",
    error_type: type[Exception] | None = None,
    match_error: str = "",
) -> Iterator[None]:
    """Assert the inverse of :func:`assert_idom_logged`"""
    try:
        with assert_idom_did_log(match_message, error_type, match_error):
            yield None
    except LogAssertionError:
        pass
    else:
        _raise_log_message_error(
            "Did find a log record matching the given",
            match_message,
            error_type,
            match_error,
        )


def list_logged_exceptions(
    log_records: list[logging.LogRecord],
    pattern: str = "",
    types: type[Any] | tuple[type[Any], ...] = Exception,
    log_level: int = logging.ERROR,
    del_log_records: bool = True,
) -> list[BaseException]:
    """Return a list of logged exception matching the given criteria

    Args:
        log_level: The level of log to check
        exclude_exc_types: Any exception types to ignore
        del_log_records: Whether to delete the log records for yielded exceptions
    """
    found: list[BaseException] = []
    compiled_pattern = re.compile(pattern)
    for index, record in enumerate(log_records):
        if record.levelno >= log_level and record.exc_info:
            error = record.exc_info[1]
            if (
                error is not None
                and isinstance(error, types)
                and compiled_pattern.search(str(error))
            ):
                if del_log_records:
                    del log_records[index - len(found)]
                found.append(error)
    return found


@contextmanager
def capture_idom_logs() -> Iterator[list[logging.LogRecord]]:
    """Capture logs from IDOM

    Any logs produced in this context are cleared afterwards
    """
    original_level = ROOT_LOGGER.level
    ROOT_LOGGER.setLevel(logging.DEBUG)
    try:
        if _LOG_RECORD_CAPTOR in ROOT_LOGGER.handlers:
            start_index = len(_LOG_RECORD_CAPTOR.records)
            try:
                yield _LOG_RECORD_CAPTOR.records
            finally:
                end_index = len(_LOG_RECORD_CAPTOR.records)
                _LOG_RECORD_CAPTOR.records[start_index:end_index] = []
            return None

        ROOT_LOGGER.addHandler(_LOG_RECORD_CAPTOR)
        try:
            yield _LOG_RECORD_CAPTOR.records
        finally:
            ROOT_LOGGER.removeHandler(_LOG_RECORD_CAPTOR)
            _LOG_RECORD_CAPTOR.records.clear()
    finally:
        ROOT_LOGGER.setLevel(original_level)


class _LogRecordCaptor(logging.NullHandler):
    def __init__(self) -> None:
        self.records: list[logging.LogRecord] = []
        super().__init__()

    def handle(self, record: logging.LogRecord) -> bool:
        self.records.append(record)
        return True


_LOG_RECORD_CAPTOR = _LogRecordCaptor()


def _raise_log_message_error(
    prefix: str,
    match_message: str = "",
    error_type: type[Exception] | None = None,
    match_error: str = "",
) -> NoReturn:
    conditions = []
    if match_message:
        conditions.append(f"log message pattern {match_message!r}")
    if error_type:
        conditions.append(f"exception type {error_type}")
    if match_error:
        conditions.append(f"error message pattern {match_error!r}")
    raise LogAssertionError(prefix + " " + " and ".join(conditions))
