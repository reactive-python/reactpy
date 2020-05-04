from typing import Any
from selenium.webdriver.remote.webelement import WebElement


def send_keys(element: WebElement, keys: Any) -> None:
    for char in keys:
        element.send_keys(char)
