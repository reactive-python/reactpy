import logging
import os

import pytest

from idom import testing
from idom.log import ROOT_LOGGER
from idom.sample import App as SampleApp


def test_assert_idom_logged_does_not_supress_errors():
    with pytest.raises(RuntimeError, match="expected error"):
        with testing.assert_idom_logged():
            raise RuntimeError("expected error")


def test_assert_idom_logged_message():
    with testing.assert_idom_logged(match_message="my message"):
        ROOT_LOGGER.info("my message")

    with testing.assert_idom_logged(match_message=r".*"):
        ROOT_LOGGER.info("my message")


def test_assert_idom_logged_error():
    with testing.assert_idom_logged(
        match_message="log message",
        error_type=ValueError,
        match_error="my value error",
    ):
        try:
            raise ValueError("my value error")
        except ValueError:
            ROOT_LOGGER.exception("log message")

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
                ROOT_LOGGER.exception("log message")

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
                ROOT_LOGGER.exception("log message")

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
                ROOT_LOGGER.exception("something else")


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
    original_level = ROOT_LOGGER.level
    ROOT_LOGGER.setLevel(logging.INFO)
    try:
        with testing.assert_idom_logged(match_message=r".*"):
            # this log would normally be ignored
            ROOT_LOGGER.debug("my message")
    finally:
        ROOT_LOGGER.setLevel(original_level)


def test_assert_idom_did_not_log():
    with testing.assert_idom_did_not_log(match_message="my message"):
        pass

    with testing.assert_idom_did_not_log(match_message=r"something else"):
        ROOT_LOGGER.info("my message")

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
                ROOT_LOGGER.exception("something")


async def test_simple_display_fixture():
    if os.name == "nt":
        pytest.skip("Browser tests not supported on Windows")
    async with testing.DisplayFixture() as display:
        await display.show(SampleApp)
        await display.page.wait_for_selector("#sample")
