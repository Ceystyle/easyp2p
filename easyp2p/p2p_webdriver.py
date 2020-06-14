# -*- coding: utf-8 -*-
#  Copyright (c) 2018-2020 Niko Sandschneider

"""
Module implementing P2PWebDriver, a class representing a P2P platform.

This module defines the P2PWebDriver class. It contains code for performing log
in, log out, opening the account statement page and generating and downloading
the account statement. It relies mainly on functionality provided by the
Selenium webdriver. easyp2p uses Chromedriver as webdriver.

"""

from datetime import date
import glob
import logging
import os
import shutil
import tempfile
import time
from typing import Mapping, Optional, Tuple

import arrow
from selenium.common.exceptions import (
    NoSuchElementException, StaleElementReferenceException, TimeoutException)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select

from easyp2p.p2p_credentials import get_credentials
from easyp2p.p2p_signals import Signals
from easyp2p.p2p_chrome import P2PChrome
from easyp2p.errors import PlatformErrors

logger = logging.getLogger('easyp2p.p2p_webdriver')


class P2PWebDriver:

    """
    Representation of P2P platform including required methods for interaction.

    Represents a P2P platform and the required methods for login/logout,
    generating and downloading account statements.

    """

    # Signals for communicating with the GUI
    signals = Signals()

    def __init__(
            self, name: str, headless: bool,
            logout_wait_until_loc: Tuple[str, str],
            logout_url: Optional[str] = None,
            logout_locator: Optional[Tuple[str, str]] = None,
            hover_locator: Optional[Tuple[str, str]] = None,
            signals: Optional[Signals] = None) -> None:
        """
        Constructor of P2P class.

        Args:
            name: Name of the P2P platform.
            headless: If True use ChromeDriver in headless mode, if False not.
            logout_wait_until_loc: Locator of web element which must be
                clickable in case of a successful logout.
            logout_url: URL of the logout page. Default is None.
            logout_locator: Locator of logout web element. Default is None.
            hover_locator: Locator of web element where the
                mouse needs to hover in order to make logout button visible.
                Default is None.
            signals: Signals instance for communicating with the calling class.

       Raises:
            RuntimeError: If no URL for login or statement page or no logout
                method is provided

        """
        self.logger = logging.getLogger('easyp2p.p2p_webdriver.P2PWebDriver')
        self.errors = PlatformErrors(name)

        if signals:
            self.signals.connect_signals(signals)

        if logout_url is None and logout_locator is None:
            # This should never happen
            raise RuntimeError(self.errors.no_logout_method)

        self.name = name
        self.driver = None
        self.headless = headless
        self.logout_wait_until_loc = logout_wait_until_loc
        self.logout_url = None
        self.logout_locator = logout_locator
        self.hover_locator = hover_locator
        self.download_dir = None
        self.logged_in = False
        self.logger.debug('%s: created P2PWebDriver instance.', self.name)

    @signals.watch_errors
    def __enter__(self) -> 'P2PWebDriver':
        """
        Start of context management protocol.

        Returns:
            Instance of P2PWebDriver class

        """
        self.download_dir = tempfile.TemporaryDirectory()
        try:
            self.driver = P2PChrome(
                self.download_dir.name, self.headless, self.signals)
        except RuntimeError as err:
            self.download_dir.cleanup()
            self.signals.disconnect_signals()
            raise RuntimeError(err)
        self.logger.debug('%s: created context manager.', self.name)
        return self

    @signals.watch_errors
    def __exit__(self, exc_type, exc_value, exc_trace) -> None:
        """
        End of context management protocol.

        If the context manager finishes the user will be logged out of the
        P2P platform. This ensures that easyp2p cleanly logs out of the website
        even in case of errors.

        Raises:
            RuntimeError: If no logout method is provided

        """
        try:
            if self.logged_in:
                if self.logout_url is not None:
                    self.logout_by_url(
                        EC.element_to_be_clickable(self.logout_wait_until_loc))
                elif self.logout_locator is not None:
                    self.logout_by_button(
                        self.logout_locator,
                        EC.element_to_be_clickable(self.logout_wait_until_loc),
                        hover_locator=self.hover_locator)
                else:
                    # Should never happen since we already check it in __init__
                    raise RuntimeWarning(self.errors.no_logout_method)

                self.logged_in = False
        finally:
            self.driver.close()
            self.download_dir.cleanup()
            self.signals.disconnect_signals()

        if exc_type:
            raise exc_type(exc_value)

        self.logger.debug('%s: context manager done.', self.name)

    @signals.update_progress
    def log_into_page(
            self, login_url: str, name_field: str, password_field: str,
            wait_until: Optional[EC.element_to_be_clickable],
            login_locator: Tuple[str, str] = None,
            fill_delay: float = 0.2) -> None:
        """
        Log into the P2P platform using the provided credentials.

        This method performs the login procedure for the P2P website.
        It opens the login page and fills in user name and password.
        Some P2P sites only show the user name and password field after
        clicking a button whose locator can be provided by the optional
        login_locator. Some P2P sites (e.g. Swaper) also require a small delay
        between filling in name and password. Otherwise it can
        sometimes happen that the password is mistakenly written
        to the name field, too.

        Args:
            login_url: URL of login page.
            name_field: Name of web element where the user name has to be
                entered
            password_field: Name of web element where the password has to be
                entered
            wait_until: Expected condition in case of successful login
            login_locator: Locator of web element which has to be clicked in
                order to open login form. Default is None.
            fill_delay: Delay in seconds between filling in password and user
                name fields. Default is 0.

        Raises:
            RuntimeError: - If login or password fields cannot be found
                          - If loading the page takes too long

        """
        self.logger.debug('%s: logging into website.', self.name)

        # Open the login page
        if login_locator is None:
            self.driver.load_url(
                login_url,
                EC.element_to_be_clickable((By.NAME, name_field)),
                self.errors.load_login_timeout)
        else:
            self.driver.load_url(
                login_url,
                EC.element_to_be_clickable(login_locator),
                self.errors.load_login_timeout)
            self.driver.click_button(
                login_locator,
                self.errors.load_login_failed,
                wait_until=EC.element_to_be_clickable((By.NAME, name_field)))

        credentials = get_credentials(self.name, self.signals)

        self.driver.enter_text(
            (By.NAME, name_field), credentials[0], self.errors.login_failed)
        time.sleep(fill_delay)
        self.driver.enter_text(
            (By.NAME, password_field), credentials[1], self.errors.login_failed,
            hit_return=True, wait_until=wait_until)

        self.logged_in = True
        self.logger.debug('%s: successfully logged in.', self.name)

    @signals.watch_errors
    def wait_for_captcha(
            self, login_url: str, locator: Tuple[str, str], text: str) -> None:
        """
        Wait for user to manually fill in recaptcha on login page.

        Args:
            login_url: URL of login page.
            locator: Locator of web element indicating invalid credentials.
            text: Text in web element indicating invalid credentials.

        Raises:
            RuntimeError: If wrong user credentials were provided.

        """
        self.logged_in = False

        while EC.url_to_be(login_url)(self.driver):
            try:
                self.driver.wait(EC.text_to_be_present_in_element(
                    locator, text), delay=1)
                raise RuntimeError(self.errors.invalid_credentials)
            except TimeoutException:
                pass
        self.logged_in = True

    @signals.update_progress
    def open_account_statement_page(
            self, statement_url: str, check_locator: Tuple[str, str]) -> None:
        """
        Open account statement page of the P2P platform.

        This function opens the account statement page of the P2P site.
        The URL of the account statement page is provided as an
        attribute of the P2P class.

        Args:
            statement_url: URL of the account statement page.
            check_locator: Locator of a web element which must be present if
                the account statement page loaded successfully

        Raises:
            RuntimeError: - If title of the page does not contain check_title
                          - If loading of page takes too long

        """
        self.logger.debug('%s: opening account statement page.', self.name)
        self.driver.load_url(
            statement_url,
            EC.presence_of_element_located(check_locator),
            self.errors.load_statement_page_failed)
        self.logger.debug(
            '%s: account statement page opened successfully.', self.name)

    @signals.update_progress
    def logout_by_button(
            self, logout_locator: Tuple[str, str],
            wait_until: EC.element_to_be_clickable,
            hover_locator: Optional[Tuple[str, str]] = None) -> None:
        """
        P2P platform logout using the provided logout button.

        This method performs the logout procedure for P2P sites
        where a button needs to be clicked to logout. For some sites the
        button only becomes clickable after hovering over a certain element.
        This element is provided by the optional hover_locator variable.

        Args:
            logout_locator: Locator of logout button
            wait_until: Expected condition in case of successful logout
            hover_locator: Locator of web element over which the mouse
                needs to hover in order to make the logout button visible.
                Default is None.

        Raises:
            RuntimeWarning: - If loading of page takes too long
                            - If the download button cannot be found

        """
        self.logger.debug('%s: starting log out by button.', self.name)
        self.driver.click_button(
            logout_locator,
            self.errors.logout_failed,
            wait_until=wait_until, hover_locator=hover_locator)
        self.logger.debug('%s: log out by button successful.', self.name)

    @signals.update_progress
    def logout_by_url(self, wait_until: EC.element_to_be_clickable) -> None:
        """
        P2P platform logout using the provided URL.

        This method performs the logout procedure for P2P sites
        where the logout page can by accessed by URL. The URL itself is
        provided in the urls dict attribute of the P2P class.

        Args:
            wait_until: Expected condition in case of successful logout

        Raises:
            RuntimeWarning: If loading of logout page takes too long

        """
        self.logger.debug('%s: starting log out by URL.', self.name)
        self.driver.load_url(
            self.logout_url, wait_until, self.errors.logout_failed)
        self.logger.debug('%s: log out by URL successful.', self.name)

    @signals.update_progress
    def generate_statement_direct(
            self, date_range: Tuple[date, date],
            start_locator: Tuple[str, str], end_locator: Tuple[str, str],
            date_format: str,
            wait_until: Optional[EC.element_to_be_clickable] = None,
            submit_btn_locator: Optional[Tuple[str, str]] = None) -> None:
        """
        Generate account statement when date fields can be edited directly.

        This method generates the account statement for P2P sites where the
        two date range fields can be edited directly. It will locate the two
        date fields, enter start and end date and then start the account
        statement generation by sending the RETURN key or optionally by
        pushing the submit button provided in the submit_btn_locator variable.

        Args:
            date_range: Date range (start_date, end_date) for which the account
                statement must be generated
            start_locator: Locator of web element where the start date needs
                to be entered
            end_locator: Locator of web element where the end date needs to be
                entered.
            date_format: Date format which the platform uses
            wait_until: Expected condition in case of successful account
                statement generation. Default is None.
            submit_btn_locator: Locator of button which needs to clicked to
                start account statement generation. Not all P2P platforms
                require this. Default is None.

        Raises:
            RuntimeError: If a web element cannot be found or if the generation
                of the account statement takes too long

        """
        self.logger.debug(
            '%s: starting direct account statement generation for '
            'date range %s.', self.name, str(date_range))

        self.driver.enter_text(
            start_locator, date.strftime(date_range[0], date_format),
            self.errors.statement_generation_failed)
        self.driver.enter_text(
            end_locator, date.strftime(date_range[1], date_format),
            self.errors.statement_generation_failed, hit_return=True)

        if submit_btn_locator:
            self.driver.click_button(
                submit_btn_locator, self.errors.statement_generation_failed,
                wait_until=wait_until)

        self.logger.debug(
            '%s: account statement generation successful.', self.name)

    @signals.update_progress
    def generate_statement_calendar(
            self, date_range: Tuple[date, date],
            month_locator: Tuple[str, str],
            prev_month_locator: Tuple[str, str],
            day_locator: Tuple[str, str],
            start_calendar: Tuple[Tuple[str, str], int],
            end_calendar: Tuple[Tuple[str, str], int],
            wait_until: Optional[EC.element_to_be_clickable] = None,
            submit_btn_locator: Optional[Tuple[str, str]] = None,
            day_class_check: Tuple[str, ...] = None) -> None:
        """
        Generate account statement by clicking days in a calendar.

        For P2P sites where the two date range fields for account
        statement generation cannot be edited directly, but must be
        clicked in a calendar. The method will locate the two calendars,
        determine how many clicks are necessary to get to the
        correct month, perform the clicks and finally locate and click
        the chosen day.

        Args:
            date_range: Date range (start_date, end_date) for which the
                account statement must be generated.
            month_locator: Locator of the web element which contains the name
                of the currently selected month.
            prev_month_locator: Locator of the web element which needs to be
                clicked to switch the calendar to the previous month.
            day_locator: Locator of the table with the days for the given month.
            start_calendar: Tuple with two elements. First element is the
                locator of the start_calendar which will be fed to
                find_elements. Second element of the tuple is the position of
                the calendar in the list returned by find_elements.
            end_calendar: Like start_calendar, just for the end date.
            wait_until: Expected condition in case of successful account
                statement generation. Default is None.
            submit_btn_locator: Locator of button which needs to clicked to
                start account statement generation. Not all P2P platforms
                require this. Default is None.
            day_class_check: For some websites the days identified by
                day_locator are not unique. They can be further specified by
                providing a tuple of class names in day_class_check.

        Raises:
            RuntimeError: - If a web element cannot be found
                          - If the generation of the account statement
                            takes too long

        """
        self.logger.debug(
            '%s: starting calendar account statement generation for '
            'date range %s.', self.name, str(date_range))

        # Set start and end date in the calendars
        self._set_date_in_calendar(
            start_calendar, date_range[0], month_locator,
            prev_month_locator, day_locator,
            day_class_check=day_class_check)
        self._set_date_in_calendar(
            end_calendar, date_range[1], month_locator,
            prev_month_locator, day_locator,
            day_class_check=day_class_check)

        if submit_btn_locator is not None:
            self.driver.click_button(
                submit_btn_locator,
                self.errors.statement_generation_failed,
                wait_until=wait_until)
        elif wait_until is not None:
            try:
                self.driver.wait(wait_until)
            except TimeoutException:
                self.logger.exception('%s: Timeout.', self.name)
                raise RuntimeError(self.errors.statement_generation_failed)

        self.logger.debug(
            '%s: account statement generation successful.', self.name)

    def _open_calendar(
            self, calendar_locator: Tuple[Tuple[str, str], int]) -> None:
        """
        Helper method for locating and opening the calendar for setting account
        statement start or end dates.

        Args:
            calendar_locator: Tuple with two elements. First element is the
                locator of the start_calendar which will be fed to
                find_elements. Second element of the tuple is the position
                of the calendar in the list returned by find_elements.

        Raises:
            RuntimeError: If the calendars could not be located.

        """
        try:
            self.driver.wait(EC.element_to_be_clickable(calendar_locator[0]))
            calendars = self.driver.find_elements(*calendar_locator[0])
            calendars[calendar_locator[1]].click()
        except (NoSuchElementException, TimeoutException):
            self.logger.exception(
                '%s: failed to locate web element.', self.name)
            raise RuntimeError(self.errors.statement_generation_failed)
        except IndexError:
            self.logger.exception(
                '%s: calendar not found in calendar list.', self.name)
            raise RuntimeError(self.errors.statement_generation_failed)

    def _set_date_in_calendar(
            self, calendar_locator: Tuple[Tuple[str, str], int],
            target_date: date,
            month_locator: Tuple[str, str],
            prev_month_locator: Tuple[str, str],
            day_locator: Tuple[str, str],
            day_class_check: Tuple[str, ...] = None) -> None:
        """
        Find and click the given day in the provided calendar.

        Args:
            calendar_locator: Tuple with two elements. First element is the
                locator of the start_calendar which will be fed to
                find_elements. Second element of the tuple is the position
                of the calendar in the list returned by find_elements.
            target_date: Date which will be set in the calendar.
            month_locator: Locator of the web element which contains the name
                of the currently selected month.
            prev_month_locator: Locator of the web element which needs to be
                clicked to switch the calendar to the previous month.
            day_locator: Locator of the table with the days for the given month.
            day_class_check: For some websites the days identified by
                day_locator are not unique. They can be further specified by
                providing a tuple of class names in day_class_check.

        Raises:
            RuntimeError: If the target day cannot be found in the calendar.

        """
        self.logger.debug(
            '%s: setting date %s in calendar.', self.name, str(target_date))

        self._open_calendar(calendar_locator)

        try:
            self._set_month_in_calendar(
                prev_month_locator, month_locator, target_date)
            self._set_day_in_calendar(
                day_locator, target_date, day_class_check)
        except RuntimeError:
            raise RuntimeError(self.errors.calendar_date_not_found)

    def _set_month_in_calendar(
            self, prev_month_locator, month_locator, target_date):
        """
            Switch calendar month to the target month.

            Args:
                prev_month_locator: Locator of the web element which needs to be
                    clicked to switch the calendar to the previous month.
                month_locator: Locator of the web element which contains the
                    name of the currently selected month.
                target_date: Target date to which the calendar has to be
                    switched.

            Raises:
                RuntimeError: If the month cannot be set in the calendar.

        """
        try:
            prev_month = self.driver.wait(
                EC.element_to_be_clickable(prev_month_locator))

            screen_date = arrow.get(
                self.driver.find_element(*month_locator).text,
                'MMMM YYYY', locale='en_US')
            while screen_date.month > target_date.month \
                    or screen_date.year > target_date.year:
                prev_month.click()
                screen_date = arrow.get(
                    self.driver.find_element(*month_locator).text,
                    'MMMM YYYY', locale='en_US')
        except (NoSuchElementException, TimeoutException):
            self.logger.exception(
                '%s: failed to set month in calendar.', self.name)
            raise RuntimeError()

    def _set_day_in_calendar(self, day_locator, target_date, day_class_check):
        """
            Find and click day in currently selected calendar month.

            Args:
                day_locator: Locator of the table with the days for the given
                    month.
                target_date: Target date to which the calendar has to be
                    switched.
                day_class_check: For some websites the days identified by
                    day_locator are not unique. They can be further specified by
                    providing a tuple of class names in day_class_check.

            Raises:
                RuntimeError: If the day or the day table cannot be found in
                    the calendar.

        """
        try:
            # Get table with all days of the selected month
            all_days = self.driver.find_elements(*day_locator)

            # Find and click the target day
            for elem in all_days:
                if elem.text == str(target_date.day):
                    if day_class_check and elem.get_attribute('class') \
                            not in day_class_check:
                        continue
                    elem.click()
                    self.logger.debug(
                        '%s: setting date %s in calendar was successful.',
                        self.name, str(target_date))
                    return
        except NoSuchElementException:
            self.logger.exception(
                '%s: failed to set day in calendar.', self.name)
            raise RuntimeError()
        except StaleElementReferenceException:
            self._set_day_in_calendar(day_locator, target_date, day_class_check)

        # If we reach this point, the day was not found in the all_days table
        raise RuntimeError()

    @signals.update_progress
    def generate_statement_combo_boxes(
            self, date_dict: Mapping[Tuple[str, str], str],
            submit_btn_locator: Tuple[str, str],
            wait_until: EC.element_to_be_clickable) -> None:
        """
        Generate account statement by selecting dates in combo boxes.

        This method generates the account statement for P2P sites where start
        and end date need to be set in combo boxes, e.g. Bondora. It will
        locate the combo boxes, select provided start/end date entries and then
        start the account statement generation by clicking the submit button.

        Args:
            date_dict: Dictionary mapping the locators of each combo box with
                the string text which should be selected in this combo box.
            submit_btn_locator: Locator of the submit button for starting
                account statement generation.
            wait_until: Expected condition in case of successful account
                statement generation.

        Raises:
            RuntimeError: If one of the web elements can not be found or if
                statement generation takes too long.

        """
        self.logger.debug(
            '%s: starting account statement generation by setting '
            'combo boxes.', self.name)
        try:
            # Change the date values to the given start and end dates
            for locator in date_dict.keys():
                select = Select(self.driver.find_element(*locator))
                select.select_by_visible_text(date_dict[locator])
        except NoSuchElementException:
            self.logger.exception('%s: failed to find combo box.', self.name)
            raise RuntimeError(self.errors.statement_generation_failed)

        # Start the account statement generation
        self.driver.click_button(
            submit_btn_locator,
            self.errors.statement_generation_failed,
            wait_until=wait_until)
        self.logger.debug(
            '%s: account statement generation was successful.', self.name)

    @signals.update_progress
    def download_statement(
            self, statement: str, download_locator: Tuple[str, str],
            actions=None) -> None:
        """
        Download account statement file by clicking the provided button.

        Downloads the generated account statement by clicking the provided
        download button. Some P2P sites require further actions before the
        button is clickable, which can be provided by the optional actions
        variable. The method also checks if the download was successful.
        If true, the _rename_statement method is called to rename the
        downloaded file to statement.

        Args:
            statement: File name including path where the downloaded
                statement should be saved.
            download_locator: Locator of the download button.
            actions: 'move to element' or None: some P2P sites require that the
                mouse hovers over the download button to make it clickable.
                Default is None.

        Raises:
            RuntimeError: If the download does not start, takes too long or
                does not finish successfully.

        """
        self.logger.debug('%s: starting account statement download.', self.name)
        if actions == 'move_to_element':
            hover_locator = download_locator
        else:
            hover_locator = None

        self.driver.click_button(
            download_locator,
            self.errors.statement_download_failed,
            hover_locator=hover_locator)

        if not self.download_finished(statement):
            raise RuntimeError(self.errors.statement_download_failed)

        self.logger.debug('%s: account statement download finished.', self.name)

    def download_finished(
            self, location: str, max_wait_time: float = 4.0) -> bool:
        """
        Wait until statement download is done and rename the file to the value
        in location.

        Args:
            location: Absolute file path where the statement should be saved.
            max_wait_time: Maximum time in seconds to wait for download to
                start/finish.

        Returns:
            True if download finished successfully, False if not.

        Raises:
            RuntimeError: If there is more than one file in the download
            directory.

        """
        done = False
        waiting_time = 0
        download_time = 0

        while not done:
            ongoing_downloads = glob.glob(
                os.path.join(self.driver.download_directory, '*.crdownload'))
            if ongoing_downloads:
                if download_time > max_wait_time:
                    logger.error('Download time exceeded max_wait_time.')
                    return False
                time.sleep(1)
                download_time += 1
            else:
                filelist = glob.glob(
                    os.path.join(self.driver.download_directory, '*'))
                if len(filelist) == 1 and not filelist[0].endswith(
                        'crdownload'):
                    shutil.move(filelist[0], location)
                    return True

                if len(filelist) > 1:
                    # This should never happen since the download directory is a
                    # newly created temporary directory
                    logger.error(
                        'More than one active download found: %s',
                        str(filelist))
                    raise RuntimeError(
                        self.errors.download_directory_not_empty(
                            self.driver.download_directory))

                if waiting_time > max_wait_time:
                    # If the download didn't start after more than max_wait_time
                    # something has gone wrong.
                    logger.error('Download did not start within max_wait_time.')
                    return False

                time.sleep(1)
                waiting_time += 1

        return False
