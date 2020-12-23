from selenium.webdriver.support.ui import WebDriverWait

import idom

from idom.testing import open_selenium_chrome_driver_and_display_context


def test_open_selenium_chrome_driver_and_display_context(driver_is_headless):
    is_clicked = idom.Ref(False)

    @idom.element
    def MyButton():
        return idom.html.button(
            {
                "onClick": lambda event: is_clicked.set_current(True),
                "id": "test-button",
            },
            "test button",
        )

    with open_selenium_chrome_driver_and_display_context(
        headless=driver_is_headless
    ) as (driver, display_context):
        with display_context() as display:
            display(MyButton)
            client_button = driver.find_element_by_id("test-button")
            client_button.click()
            WebDriverWait(driver, timeout=3).until(lambda d: is_clicked.current)
