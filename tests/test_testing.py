import logging

import pytest

from idom import testing
from idom.log import ROOT_LOGGER as logger


def test_assert_idom_logged_does_not_supress_errors():
    with pytest.raises(RuntimeError, match="expected error"):
        with testing.assert_idom_logged():
            raise RuntimeError("expected error")


def test_assert_idom_logged_message():
    with testing.assert_idom_logged(match_message="my message"):
        logger.info("my message")

    with testing.assert_idom_logged(match_message=r".*"):
        logger.info("my message")


def test_assert_idom_logged_error():
    with testing.assert_idom_logged(
        match_message="log message",
        error_type=ValueError,
        match_error="my value error",
    ):
        try:
            raise ValueError("my value error")
        except ValueError:
            logger.exception("log message")

    with pytest.raises(
        AssertionError,
        match=r"Could not find a log record matching the given",
    ):
        with testing.assert_idom_logged(
            match_message="log message",
            error_type=ValueError,
            match_error="my value error",
        ):
            try:
                # change error type
                raise RuntimeError("my value error")
            except RuntimeError:
                logger.exception("log message")

    with pytest.raises(
        AssertionError,
        match=r"Could not find a log record matching the given",
    ):
        with testing.assert_idom_logged(
            match_message="log message",
            error_type=ValueError,
            match_error="my value error",
        ):
            try:
                # change error message
                raise ValueError("something else")
            except ValueError:
                logger.exception("log message")

    with pytest.raises(
        AssertionError,
        match=r"Could not find a log record matching the given",
    ):
        with testing.assert_idom_logged(
            match_message="log message",
            error_type=ValueError,
            match_error="my value error",
        ):
            try:
                # change error message
                raise ValueError("my error message")
            except ValueError:
                logger.exception("something else")


def test_assert_idom_logged_assertion_error_message():
    with pytest.raises(
        AssertionError,
        match=r"Could not find a log record matching the given",
    ):
        with testing.assert_idom_logged(
            # put in all possible params full assertion error message
            match_message=r".*",
            error_type=Exception,
            match_error=r".*",
        ):
            pass


def test_assert_idom_logged_ignores_level():
    original_level = logger.level
    logger.setLevel(logging.INFO)
    try:
        with testing.assert_idom_logged(match_message=r".*"):
            # this log would normally be ignored
            logger.debug("my message")
    finally:
        logger.setLevel(original_level)


def test_assert_idom_did_not_log():
    with testing.assert_idom_did_not_log(match_message="my message"):
        pass

    with testing.assert_idom_did_not_log(match_message=r"something else"):
        logger.info("my message")

    with pytest.raises(
        AssertionError,
        match=r"Did find a log record matching the given",
    ):
        with testing.assert_idom_did_not_log(
            # put in all possible params full assertion error message
            match_message=r".*",
            error_type=Exception,
            match_error=r".*",
        ):
            try:
                raise Exception("something")
            except Exception:
                logger.exception("something")
