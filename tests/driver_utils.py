from typing import Any

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement


def send_keys(element: WebElement, keys: Any) -> None:
    for char in keys:
        element.send_keys(char)


def no_such_element(driver: WebDriver, method: str, param: Any) -> bool:
    try:
        driver.find_element(method, param)
    except NoSuchElementException:
        return True
    else:
        return False
