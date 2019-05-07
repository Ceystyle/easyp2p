# -*- coding: utf-8 -*-
# Copyright 2019 Niko Sandschneider

"""Module implementing P2PWebDriver."""

import os
from typing import Callable, cast, List

from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException, WebDriverException)
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class P2PWebDriver(webdriver.Chrome):

    """A class for providing webdriver support to easyp2p."""

    def __init__(self, download_directory: str, headless: bool) -> None:
        """
        Initialize the P2PWebDriver class.

        Args:
            download_directory: Will be set as download directory for the
                Chromedriver
            headless: If True run Chromedriver in headless mode

        """
        self.download_directory = download_directory
        self.headless = headless
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
        if self.headless:
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

        if self.headless:
            # This is needed to allow downloads in headless mode
            params = {
                'behavior': 'allow', 'downloadPath': self.download_directory}
            self.execute_cdp_cmd('Page.setDownloadBehavior', params)

        return self

    def wait(self, wait_until: EC, delay: float = 5.0) -> WebElement:
        """
        Shorthand for WebDriverWait.

        Args:
            wait_until: Expected condition for which the webdriver should wait
            delay: Maximal waiting time in seconds. Default is 5.0.

        Returns:
            WebElement which WebDriverWait waited for.

        """
        return WebDriverWait(self, delay).until(wait_until)


class WebDriverNotFound(Exception):
    """Custom exception which will be raised if Chromedriver cannot be found."""


class one_of_many_expected_conditions_true:
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
