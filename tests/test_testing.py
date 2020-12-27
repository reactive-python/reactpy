from selenium.webdriver.support.ui import WebDriverWait

import idom

from idom.testing import open_selenium_driver_and_mount


def test_open_driver_and_mount(driver_is_headless):
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

    with open_selenium_driver_and_mount(headless=driver_is_headless) as (
        driver,
        display_context,
    ):
        with display_context() as display:
            display(MyButton)
            client_button = driver.find_element_by_id("test-button")
            client_button.click()
            WebDriverWait(driver, timeout=3).until(lambda d: is_clicked.current)
