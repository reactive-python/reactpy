from typing import Any
from selenium.webdriver.remote.webelement import WebElement


def send_keys(element: WebElement, *values: Any) -> None:
    for keys in values:
        for char in keys:
            element.send_keys(char)
