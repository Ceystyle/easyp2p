# -*- coding: utf-8 -*-
# Copyright 2019 Niko Sandschneider

"""
Module implementing PlatformWebDriver.

"""
import os
from typing import cast, Optional, Tuple

from selenium import webdriver
from selenium.common.exceptions import WebDriverException

from easyp2p.p2p_platform import P2PPlatform

class PlatformWebDriver:

    """
    A class providing webdriver functionality for easyp2p.

    """

    def __init__(
            self, platform: P2PPlatform, logout_wait_until: bool,
            logout_locator: Optional[Tuple[str, str]] = None,
            hover_locator: Optional[Tuple[str, str]] = None) -> None:
        """
        Constructor of PlatformWebDriver class.

        Args:
            platform: Instance of P2PPlatform class
            logout_wait_until: Expected condition in case
                of successful logout

        Keyword Args:
            logout_locator: Locator of logout web element
            hover_locator: Locator of web element where the
                mouse needs to hover in order to make logout button visible

       Raises:
            RuntimeError: If no logout method is provided

        """
        self.platform = platform
        self.logout_wait_until = logout_wait_until
        self.logout_locator = logout_locator
        self.hover_locator = hover_locator
        self.logged_in = False

        if 'logout' not in self.platform.urls and self.logout_locator is None:
            raise RuntimeError(
                '{0}: Keine Methode für Logout vorhanden!'.format(
                    self.platform.name))

        # self.driver will be initialized in __enter__ method to make sure it
        # is always closed again by __exit__
        self.driver = cast(webdriver.Chrome, None)

    def __enter__(self) -> 'PlatformWebDriver':
        """
        Start of context management protocol.

        Returns:
            Instance of PlatformWebDriver class

        """
        self.init_webdriver()
        self.platform.driver = self.driver
        return self

    def __exit__(self, exc_type, exc_value, exc_trace) -> None:
        """
        End of context management protocol.

        Raises:
            RuntimeError: If no logout method is provided

        """
        if self.logged_in:
            if 'logout' in self.platform.urls:
                self.platform.logout_by_url(self.logout_wait_until)
            elif self.logout_locator is not None:
                self.platform.logout_by_button(
                    self.logout_locator,
                    self.logout_wait_until,
                    hover_locator=self.hover_locator)
            else:
                # This should never happen
                raise RuntimeError(
                    '{0}: Keine Methode für Logout vorhanden!'
                    .format(self.platform.name))

            self.logged_in = False

        self.driver.close()
        if exc_type:
            raise exc_type(exc_value)

    def init_webdriver(self) -> None:
        """
        Initialize Chromedriver as webdriver.

        Initializes Chromedriver as webdriver, sets the default download
        location to p2p_downloads relative to the current working directory
        and opens a new maximized browser window.

        Raises:
            ModuleNotFoundError: If Chromedriver cannot be found

        """
        options = webdriver.ChromeOptions()
#        options.add_argument("--headless")
#        options.add_argument("--window-size=1920,1200")
        prefs = {"download.default_directory": os.path.dirname(
            self.platform.statement_file_name)}
        options.add_experimental_option("prefs", prefs)

        # TODO: Ubuntu doesn't put chromedriver in PATH so we need to
        # explicitly specify its location. Find a better solution that works on
        # all systems.
        try:
            if os.path.isfile('/usr/lib/chromium-browser/chromedriver'):
                driver = webdriver.Chrome(
                    executable_path=r'/usr/lib/chromium-browser/chromedriver',
                    options=options)
            else:
                driver = webdriver.Chrome(options=options)
        except WebDriverException:
            raise ModuleNotFoundError(
                'Chromedriver konnte nicht gefunden werden!\n'
                'easyp2p wird beendet!')

        driver.maximize_window()
        self.driver = driver
