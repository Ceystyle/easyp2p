# -*- coding: utf-8 -*-
# Copyright 2019 Niko Sandschneider

"""Module implementing P2PWebDriver."""

import os
from typing import Callable, cast, List, Optional, Union

from selenium.common.exceptions import (
    NoSuchElementException, WebDriverException)
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from PyQt5.QtCore import QCoreApplication

from easyp2p.p2p_signals import Signals

_translate = QCoreApplication.translate


class P2PWebDriver(Chrome):

    """A class for providing webdriver support to easyp2p."""

    # Signals for communicating with the GUI
    signals = Signals()

    @signals.update_progress
    def __init__(
            self, download_directory: str, headless: bool,
            signals: Optional[Signals] = None) -> None:
        """
        Initialize the P2PWebDriver class.

        Args:
            download_directory: Will be set as download directory for the
                ChromeDriver
            headless: If True run ChromeDriver in headless mode

        """
        self.download_directory = download_directory
        self.driver = cast(Chrome, None)
        options = ChromeOptions()
        prefs = {"download.default_directory": self.download_directory}
        options.add_experimental_option("prefs", prefs)
        options.add_argument("start-maximized")
        options.binary_location = "/usr/bin/chromium"
        if headless:
            options.add_argument("--headless")
            options.add_argument("--window-size=1920,1200")
        if signals:
            self.signals.connect_signals(signals)

        # Ubuntu doesn't put ChromeDriver in PATH so we need to
        # explicitly specify its location.
        # TODO: Find a better solution that works on all systems.
        try:
            if os.path.isfile('/usr/lib/chromium-browser/chromedriver'):
                super().__init__(
                    executable_path=r'/usr/lib/chromium-browser/chromedriver',
                    options=options)
            else:
                super().__init__(options=options)
        except WebDriverException:
            linux_command = '\n\n\tsudo apt-get install chromium-driver\n\n'
            download_link = '\n\nhttps://sites.google.com/a/chromium.org' \
                '/chromedriver/downloads\n\n'
            self.signals.end_easyp2p.emit(_translate(
                'P2PWebDriver', 'ChromeDriver could not be found!\n\n'
                'In Linux this can usually be fixed by:'
                f'\n\n\t{linux_command}\n\n'
                'In Windows ChromeDriver can be downloaded from:'
                f'\n\n{download_link}\n\n'
                'easyp2p will be aborted now!'),
                _translate('WorkerThread', 'ChromeDriver not found!'))
            raise RuntimeError('ChromeDriver not found!')

        if headless:
            # This is needed to allow downloads in headless mode
            params = {
                'behavior': 'allow', 'downloadPath': self.download_directory}
            self.execute_cdp_cmd('Page.setDownloadBehavior', params)

    def __exit__(self, exc_type, exc_val, exc_tb):
        super().__exit__(self, exc_type, exc_val, exc_tb)
        self.signals.disconnect_signals()

    def wait(
            self, wait_until: EC, delay: float = 15.0) -> WebElement:
        """
        Shorthand for WebDriverWait.

        Args:
            wait_until: Expected condition for which the webdriver should wait
            delay: Maximal waiting time in seconds. Default is 5.0.

        Returns:
            WebElement which WebDriverWait waited for.

        """
        return WebDriverWait(self, delay).until(wait_until)


class one_of_many_expected_conditions_true:
    """
    An expectation for checking if (at least) one of several provided expected
    conditions for the Selenium webdriver is true.
    """
    def __init__(self, conditions: List[Callable[[Chrome], bool]]) -> None:
        """
        Initialize class.

        Args:
            conditions: List of all conditions which should be checked.

        """
        self.conditions = conditions

    def __call__(self, driver: Chrome) -> bool:
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


# Helper for type hints
expected_conditions = Union[
    EC.element_to_be_clickable, one_of_many_expected_conditions_true]
