import logging
import os

import pytest

from reactpy import Ref, component, html, testing
from reactpy.backend import starlette as starlette_implementation
from reactpy.logging import ROOT_LOGGER
from reactpy.sample import SampleApp
from reactpy.testing.backend import _hotswap
from reactpy.testing.display import DisplayFixture


def test_assert_reactpy_logged_does_not_suppress_errors():
    with pytest.raises(RuntimeError, match="expected error"):
        with testing.assert_reactpy_did_log():
            msg = "expected error"
            raise RuntimeError(msg)


def test_assert_reactpy_logged_message():
    with testing.assert_reactpy_did_log(match_message="my message"):
        ROOT_LOGGER.info("my message")

    with testing.assert_reactpy_did_log(match_message=r".*"):
        ROOT_LOGGER.info("my message")


def test_assert_reactpy_logged_error():
    with testing.assert_reactpy_did_log(
        match_message="log message",
        error_type=ValueError,
        match_error="my value error",
    ):
        try:
            msg = "my value error"
            raise ValueError(msg)
        except ValueError:
            ROOT_LOGGER.exception("log message")

    with pytest.raises(
        AssertionError,
        match=r"Could not find a log record matching the given",
    ):
        with testing.assert_reactpy_did_log(
            match_message="log message",
            error_type=ValueError,
            match_error="my value error",
        ):
            try:
                # change error type
                msg = "my value error"
                raise RuntimeError(msg)
            except RuntimeError:
                ROOT_LOGGER.exception("log message")

    with pytest.raises(
        AssertionError,
        match=r"Could not find a log record matching the given",
    ):
        with testing.assert_reactpy_did_log(
            match_message="log message",
            error_type=ValueError,
            match_error="my value error",
        ):
            try:
                # change error message
                msg = "something else"
                raise ValueError(msg)
            except ValueError:
                ROOT_LOGGER.exception("log message")

    with pytest.raises(
        AssertionError,
        match=r"Could not find a log record matching the given",
    ):
        with testing.assert_reactpy_did_log(
            match_message="log message",
            error_type=ValueError,
            match_error="my value error",
        ):
            try:
                # change error message
                msg = "my error message"
                raise ValueError(msg)
            except ValueError:
                ROOT_LOGGER.exception("something else")


def test_assert_reactpy_logged_assertion_error_message():
    with pytest.raises(
        AssertionError,
        match=r"Could not find a log record matching the given",
    ):
        with testing.assert_reactpy_did_log(
            # put in all possible params full assertion error message
            match_message=r".*",
            error_type=Exception,
            match_error=r".*",
        ):
            pass


def test_assert_reactpy_logged_ignores_level():
    original_level = ROOT_LOGGER.level
    ROOT_LOGGER.setLevel(logging.INFO)
    try:
        with testing.assert_reactpy_did_log(match_message=r".*"):
            # this log would normally be ignored
            ROOT_LOGGER.debug("my message")
    finally:
        ROOT_LOGGER.setLevel(original_level)


def test_assert_reactpy_did_not_log():
    with testing.assert_reactpy_did_not_log(match_message="my message"):
        pass

    with testing.assert_reactpy_did_not_log(match_message=r"something else"):
        ROOT_LOGGER.info("my message")

    with pytest.raises(
        AssertionError,
        match=r"Did find a log record matching the given",
    ):
        with testing.assert_reactpy_did_not_log(
            # put in all possible params full assertion error message
            match_message=r".*",
            error_type=Exception,
            match_error=r".*",
        ):
            try:
                msg = "something"
                raise Exception(msg)
            except Exception:
                ROOT_LOGGER.exception("something")


async def test_simple_display_fixture():
    if os.name == "nt":
        pytest.skip("Browser tests not supported on Windows")
    async with testing.DisplayFixture() as display:
        await display.show(SampleApp)
        await display.page.wait_for_selector("#sample")


def test_if_app_is_given_implementation_must_be_too():
    with pytest.raises(
        ValueError,
        match=r"If an application instance its corresponding server implementation must be provided too",
    ):
        testing.BackendFixture(app=starlette_implementation.create_development_app())

    testing.BackendFixture(
        app=starlette_implementation.create_development_app(),
        implementation=starlette_implementation,
    )


def test_list_logged_excptions():
    the_error = None
    with testing.capture_reactpy_logs() as records:
        ROOT_LOGGER.info("A non-error log message")

        try:
            msg = "An error for testing"
            raise ValueError(msg)
        except Exception as error:
            ROOT_LOGGER.exception("Log the error")
            the_error = error

        logged_errors = testing.logs.list_logged_exceptions(records)
        assert logged_errors == [the_error]


async def test_hostwap_update_on_change(display: DisplayFixture):
    """Ensure shared hotswapping works

    This basically means that previously rendered views of a hotswap component get updated
    when a new view is mounted, not just the next time it is re-displayed

    In this test we construct a scenario where clicking a button will cause a pre-existing
    hotswap component to be updated
    """

    def make_next_count_constructor(count):
        """We need to construct a new function so they're different when we set_state"""

        def constructor():
            count.current += 1
            return html.div({"id": f"hotswap-{count.current}"}, count.current)

        return constructor

    @component
    def ButtonSwapsDivs():
        count = Ref(0)

        async def on_click(event):
            mount(make_next_count_constructor(count))

        incr = html.button({"on_click": on_click, "id": "incr-button"}, "incr")

        mount, make_hostswap = _hotswap(update_on_change=True)
        mount(make_next_count_constructor(count))
        hotswap_view = make_hostswap()

        return html.div(incr, hotswap_view)

    await display.show(ButtonSwapsDivs)

    client_incr_button = await display.page.wait_for_selector("#incr-button")

    await display.page.wait_for_selector("#hotswap-1")
    await client_incr_button.click()
    await display.page.wait_for_selector("#hotswap-2")
    await client_incr_button.click()
    await display.page.wait_for_selector("#hotswap-3")
