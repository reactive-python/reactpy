from typing import Any
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.remote.webdriver import WebDriver


def send_keys(element: WebElement, keys: Any) -> None:
    for char in keys:
        element.send_keys(char)


def no_such_element(driver: WebDriver, method: str, param: Any) -> bool:
    try:
        getattr(driver, f"find_element_by_{method}")(param)
    except NoSuchElementException:
        return True
    else:
        raise False
