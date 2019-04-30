# -*- coding: utf-8 -*-
# Copyright 2019 Niko Sandschneider

"""Module implementing P2PWebDriver."""

import os
from typing import Callable, cast, List

from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException, WebDriverException)
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait

from easyp2p.p2p_settings import Settings


class P2PWebDriver(webdriver.Chrome):

    """A class for providing webdriver support to easyp2p."""

    def __init__(self, download_directory: str, settings: Settings) -> None:
        """
        Initialize the P2PWebDriver class.

        Args:
            download_directory: Will be set as download directory for the
                Chromedriver
            settings: Settings for easyp2p

        """
        self.download_directory = download_directory
        self.settings = settings
        self.driver = cast(webdriver.Chrome, None)

    def __enter__(self) -> 'P2PWebDriver':
        """
        Initialize ChromeDriver as webdriver.

        Initializes Chromedriver as webdriver, sets the download directory
        and opens a new maximized browser window.

        Raises:
            ModuleNotFoundError: If Chromedriver cannot be found

        """
        options = webdriver.ChromeOptions()
        prefs = {"download.default_directory": self.download_directory}
        options.add_experimental_option("prefs", prefs)
        options.add_argument("start-maximized")
        if self.settings.headless:
            options.add_argument("--headless")
            options.add_argument("--window-size=1920,1200")
        # Ubuntu doesn't put chromedriver in PATH so we need to
        # explicitly specify its location.
        # TODO: Find a better solution that works on all systems.
        try:
            if os.path.isfile('/usr/lib/chromium-browser/chromedriver'):
                super().__init__(
                    executable_path=r'/usr/lib/chromium-browser/chromedriver',
                    options=options)
            else:
                super().__init__(options=options)
        except WebDriverException as err:
            raise WebDriverNotFound(
                'Chromedriver konnte nicht gefunden werden!\n'
                'easyp2p wird beendet!\n', err)

        if self.settings.headless:
            # This is needed to allow downloads in headless mode
            self.command_executor._commands["send_command"] = (
                "POST", '/session/$sessionId/chromium/send_command')
            params = {'cmd': 'Page.setDownloadBehavior', 'params': {
                'behavior': 'allow', 'downloadPath': self.download_directory}}
            self.execute("send_command", params)

        return self

    def __exit__(self, exc_type, exc_value, exc_trace) -> None:
        """Close the WebDriver."""
        self.close()

    def wait(self, wait_until: bool, delay: float = 5.0) -> WebElement:
        """
        Shorthand for WebDriverWait.

        Args:
            wait_until: Expected condition for which the webdriver should wait

        Keyword Args:
            delay: Maximal waiting time in seconds

        Returns:
            WebElement which WebDriverWait waited for.

        """
        return WebDriverWait(self, delay).until(wait_until)


class WebDriverNotFound(Exception):
    """Custom exception which will be raised if Chromedriver cannot be found."""


class one_of_many_expected_conditions_true():
    """
    An expectation for checking if (at least) one of several provided expected
    conditions for the Selenium webdriver is true.
    """
    def __init__(self, conditions: List[Callable[[webdriver.Chrome], bool]]) \
            -> None:
        """
        Initialize class.

        Args:
            conditions: List of all conditions which should be checked.

        """
        self.conditions = conditions

    def __call__(self, driver: webdriver.Chrome) -> bool:
        """
        Caller for class.

        Args:
            driver: Selenium webdriver

        Returns:
            True if at least one of the conditions is true, False otherwise.

        """
        for condition in self.conditions:
            try:
                if condition(driver):
                    return True
            except NoSuchElementException:
                pass
        return False
