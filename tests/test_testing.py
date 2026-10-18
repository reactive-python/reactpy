import logging
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from reactpy import Ref, component, html, testing
from reactpy.logging import ROOT_LOGGER
from reactpy.testing.backend import BackendFixture, _hotswap
from reactpy.testing.display import DisplayFixture
from tests.sample import SampleApp


def test_assert_reactpy_logged_does_not_suppress_errors():
    with pytest.raises(RuntimeError, match=r"expected error"):
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


async def test_simple_display_fixture(browser):
    async with testing.DisplayFixture(browser=browser) as display:
        await display.show(SampleApp)
        await display.page.wait_for_selector("#sample")


def test_list_logged_exceptions():
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


async def test_hotswap_update_on_change(display: DisplayFixture):
    """Ensure shared hotswapping works

    This basically means that previously rendered views of a hotswap component get updated
    when a new view is mounted, not just the next time it is re-displayed

    In this test we construct a scenario where clicking a button will cause a pre-existing
    hotswap component to be updated
    """

    def hotswap_1():
        return html.div({"id": "hotswap-1"}, 1)

    def hotswap_2():
        return html.div({"id": "hotswap-2"}, 2)

    def hotswap_3():
        return html.div({"id": "hotswap-3"}, 3)

    @component
    def ButtonSwapsDivs():
        count = Ref(0)
        mount, hostswap = _hotswap(update_on_change=True)

        async def on_click(event):
            count.set_current(count.current + 1)
            if count.current == 1:
                mount(hotswap_1)
            if count.current == 2:
                mount(hotswap_2)
            if count.current == 3:
                mount(hotswap_3)

        return html.div(
            html.button({"onClick": on_click, "id": "incr-button"}, "incr"),
            hostswap(),
        )

    await display.show(ButtonSwapsDivs)

    client_incr_button = await display.page.wait_for_selector("#incr-button")

    await client_incr_button.click()
    await display.page.wait_for_selector("#hotswap-1")
    await client_incr_button.click()
    await display.page.wait_for_selector("#hotswap-2")
    await client_incr_button.click()
    await display.page.wait_for_selector("#hotswap-3")


@pytest.mark.asyncio
async def test_backend_server_failure():
    # We need to mock uvicorn.Server to fail starting
    with patch("uvicorn.Server") as mock_server_cls:
        mock_server = mock_server_cls.return_value
        mock_server.started = False
        mock_server.servers = []
        mock_server.config.get_loop_factory = MagicMock()

        # Mock serve to just return (or sleep briefly then return)
        mock_server.serve = AsyncMock(return_value=None)

        backend = BackendFixture()

        # We need to speed up the loop
        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(RuntimeError, match="Server failed to start"):
                await backend.__aenter__()


@pytest.mark.asyncio
async def test_display_fixture_headless_logic():
    # Mock async_playwright to avoid launching real browser
    with patch("reactpy.testing.display.async_playwright") as mock_pw:
        mock_context_manager = mock_pw.return_value
        mock_playwright_instance = AsyncMock()
        mock_context_manager.__aenter__.return_value = mock_playwright_instance

        mock_browser = AsyncMock()
        mock_browser.__aenter__ = AsyncMock(return_value=mock_browser)
        mock_playwright_instance.chromium.launch.return_value = mock_browser

        mock_page = AsyncMock()
        # Configure synchronous methods on page
        mock_page.set_default_timeout = MagicMock()
        mock_page.set_default_navigation_timeout = MagicMock()
        mock_page.on = MagicMock()
        mock_page.__aenter__ = AsyncMock(return_value=mock_page)

        mock_browser.new_page.return_value = mock_page

        # Case: headless=False, PLAYWRIGHT_VISIBLE='1'
        with patch.dict(os.environ, {"PLAYWRIGHT_VISIBLE": "1"}):
            async with DisplayFixture():
                pass
            mock_playwright_instance.chromium.launch.assert_called_with(headless=False)

        # Case: headless=True, PLAYWRIGHT_VISIBLE='0'
        with patch.dict(os.environ, {"PLAYWRIGHT_VISIBLE": "0"}):
            async with DisplayFixture():
                pass
            mock_playwright_instance.chromium.launch.assert_called_with(headless=True)


@pytest.mark.asyncio
async def test_display_fixture_internal_backend():
    # This covers line 87: await self.backend_exit_stack.aclose()
    # when backend is internal (default)

    with patch("reactpy.testing.display.async_playwright") as mock_pw:
        mock_context_manager = mock_pw.return_value
        mock_playwright_instance = AsyncMock()
        mock_context_manager.__aenter__.return_value = mock_playwright_instance

        mock_browser = AsyncMock()
        mock_browser.__aenter__ = AsyncMock(return_value=mock_browser)
        mock_playwright_instance.chromium.launch.return_value = mock_browser

        mock_page = AsyncMock()
        mock_page.set_default_timeout = MagicMock()
        mock_page.set_default_navigation_timeout = MagicMock()
        mock_page.on = MagicMock()
        mock_page.__aenter__ = AsyncMock(return_value=mock_page)
        mock_browser.new_page.return_value = mock_page

        # We also need to mock BackendFixture to avoid starting real server
        with patch("reactpy.testing.display.BackendFixture") as mock_backend_cls:
            mock_backend = AsyncMock()
            mock_backend.mount = MagicMock()  # mount is synchronous
            mock_backend_cls.return_value = mock_backend

            async with DisplayFixture() as display:
                assert not display.backend_is_external

            # Verify backend exit stack closed (implied if no error and backend.__aexit__ called)
            mock_backend.__aexit__.assert_called()
