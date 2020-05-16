# -*- coding: utf-8 -*-
#  Copyright (c) 2018-2020 Niko Sandschneider

"""Module implementing P2PWebDriver."""

import logging
import os
from typing import cast, Optional, Tuple

from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import (
    NoSuchElementException, StaleElementReferenceException, TimeoutException,
    WebDriverException)
from selenium.webdriver.common.keys import Keys
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
        self.logger = logging.getLogger('easyp2p.p2p_webdriver')
        self.driver = cast(Chrome, None)
        options = ChromeOptions()
        prefs = {"download.default_directory": self.download_directory}
        options.add_experimental_option("prefs", prefs)
        options.add_argument("--start-maximized")
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
            self.logger.exception('Error opening ChromeDriver.')
            linux_command = '\n\n\tsudo apt-get install chromium-driver\n\n'
            download_link = '\n\nhttps://sites.google.com/a/chromium.org' \
                '/chromedriver/downloads\n\n'
            self.signals.end_easyp2p.emit(
                _translate(
                    'P2PWebDriver',
                    'ChromeDriver could not be found!\n\n'
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

    def __exit__(self, *args):
        self.signals.disconnect_signals()
        super().__exit__(self, *args)

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

    @signals.watch_errors
    def click_button(
            self, locator: Tuple[str, str], error_msg: str,
            wait_until: Optional[EC.element_to_be_clickable] = None,
            hover_locator: Tuple[str, str] = None,
            raise_error: bool = True) -> None:
        """
        Helper method for clicking a button. The webdriver waits until the
        button specified by locator is clickable. If wait_until is specified
        it also checks if the click was successful.

        Args:
            locator: Locator of the button to be clicked.
            error_msg: Error message in case the click is not successful.
            wait_until: Expected condition in case of successful click.
            hover_locator: Locator of a web element where the mouse needs to
                hover over in order to make the button clickable.
            raise_error: If True raise RuntimeError if clicking the button
                fails, if False just continue.

        Raises:
            RuntimeError: If the web element cannot be found or if the
                wait_until check is not successful.

        """
        try:
            if hover_locator is not None:
                elem = self.find_element(*hover_locator)
                hover = ActionChains(self).move_to_element(elem)
                hover.perform()

            self.wait(EC.element_to_be_clickable(locator)).click()
            if wait_until is not None:
                self.wait(wait_until)
        except (NoSuchElementException, TimeoutException):
            self.logger.exception('Could not click button %s.', locator)
            if raise_error:
                raise RuntimeError(error_msg)

    @signals.watch_errors
    def load_url(self, url: str, wait_until: EC, error_msg: str) -> None:
        """
        Helper method for loading a web page.

        Args:
            url: URL of the web page.
            wait_until: Expected condition in case of successful load.
            error_msg: Error message in case the page cannot be loaded.

        Raises:
            RuntimeError: If the web page cannot be loaded.

        """
        try:
            self.get(url)
            self.wait(wait_until)
        except TimeoutException:
            self.logger.exception('Could not load URL %s.', url)
            raise RuntimeError(error_msg)

    @signals.watch_errors
    def enter_text(
            self, locator: Tuple[str, str], text: str, error_msg: str,
            hit_return: bool = False,
            wait_until: Optional[EC.element_to_be_clickable] = None) -> None:
        """
            Helper method for inserting text into a web element.

            Args:
                locator: Locator of the text web element.
                text: Text to be filled in.
                error_msg: Error message in case the text cannot be inserted.
                hit_return: If True, push return key after inserting text.
                wait_until: Expected condition in case of success.

            Raises:
                RuntimeError: If inserting the text fails.

        """
        try:
            elem = self.wait(EC.element_to_be_clickable(locator))
            elem.send_keys(Keys.CONTROL + 'a')
            elem.send_keys(text)
            if hit_return:
                elem.send_keys(Keys.RETURN)
            if wait_until:
                self.wait(wait_until)
        except (NoSuchElementException, TimeoutException):
            self.logger.exception(
                'Could not fill %s in field %s.', text, locator)
            raise RuntimeError(error_msg)
        except StaleElementReferenceException:
            self.enter_text(locator, text, error_msg, hit_return, wait_until)

    def wait_and_reload(
            self, url: str, wait_until: EC.element_to_be_clickable,
            reload_freq: int, max_wait_time: int, error_msg: str) -> None:
        """
            Helper method for waiting for an expected condition to be true.
            After each unsuccessful waiting period the web page will be
            reloaded. This method is necessary for some P2P platforms, e.g.
            Robocash, where certain web elements appear only after a refresh
            of the page.

            Args:
                url: URL of the web page.
                wait_until: Expected condition for which to wait.
                reload_freq: Frequency in seconds for reloading the page and
                    checking for wait_until again.
                max_wait_time: Maximum waiting time. If wait_until is still
                    not True after max_wait_time, an error is raised.
                error_msg: Error message if wait is not successful after
                    max_wait_time.

            Raises:
                RuntimeError: If wait_until is not True after max_wait_time.

        """
        wait_time = 0

        while True:
            try:
                self.logger.debug(
                    'Reloading %s and wait for %s. Total waiting time: %d.',
                    url, str(wait_until), max_wait_time)
                self.get(url)
                self.wait(wait_until, delay=reload_freq)
                break
            except TimeoutException:
                wait_time += reload_freq
                if wait_time > max_wait_time:
                    raise RuntimeError(error_msg)
