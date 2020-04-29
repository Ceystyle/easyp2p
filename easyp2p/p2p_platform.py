# -*- coding: utf-8 -*-
# Copyright 2018-19 Niko Sandschneider

"""
Module implementing P2PPlatform, a class representing a P2P platform.

This module defines the P2PPlatform class. It contains code for performing log
in, log out, opening the account statement page and generating and downloading
the account statement. It relies mainly on functionality provided by the
Selenium webdriver. easyp2p uses Chromedriver as webdriver.

"""

from datetime import date
import glob
import logging
import os
import shutil
import time
from typing import Mapping, Optional, Tuple

import arrow
from selenium.common.exceptions import (
    ElementClickInterceptedException, NoSuchElementException,
    StaleElementReferenceException, TimeoutException)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from PyQt5.QtCore import QCoreApplication

from easyp2p.p2p_signals import Signals
from easyp2p.p2p_webdriver import P2PWebDriver, expected_conditions

_translate = QCoreApplication.translate
logger = logging.getLogger('easyp2p.p2p_platform')


class P2PPlatform:

    """
    Representation of P2P platform including required methods for interaction.

    Represents a P2P platform and the required methods for login/logout,
    generating and downloading account statements.

    """

    # Signals for communicating with the GUI
    signals = Signals()

    def __init__(
            self, name: str, driver: P2PWebDriver, urls: Mapping[str, str],
            logout_wait_until: expected_conditions,
            logout_locator: Optional[Tuple[str, str]] = None,
            hover_locator: Optional[Tuple[str, str]] = None,
            signals: Optional[Signals] = None) -> None:
        """
        Constructor of P2P class.

        Args:
            name: Name of the P2P platform
            driver: Instance of P2PWebDriver class
            urls: Dictionary with URLs for login page
                (key: 'login'), account statement page (key: 'statement')
                and optionally logout page (key: 'logout')
            logout_wait_until: Expected condition in case
                of successful logout
            logout_locator: Locator of logout web element
            hover_locator: Locator of web element where the
                mouse needs to hover in order to make logout button visible
            signals: Signals instance for communicating with the calling class.

       Raises:
            RuntimeError: If no URL for login or statement page or no logout
                method is provided

        """
        self.name = name
        self.driver = driver
        self.urls = urls
        self.logout_wait_until = logout_wait_until
        self.logout_locator = logout_locator
        self.hover_locator = hover_locator
        if signals:
            self.signals.connect_signals(signals)
        self.logged_in = False
        self.logger = logging.getLogger('easyp2p.p2p_platform.P2PPlatform')
        self.logger.debug(f'Created P2PPlatform instance for {self.name}.')

        # Make sure URLs for login and statement page are provided
        if 'login' not in urls:
            raise RuntimeError(_translate(
                'P2PPlatform', f'{self.name}: no login URL found!'))
        if 'statement' not in urls:
            raise RuntimeError(_translate(
                'P2PPlatform', f'{self.name}: no account statement URL found!'))

        # Make sure a logout method was provided
        if 'logout' not in self.urls and self.logout_locator is None:
            raise RuntimeError(_translate(
                'P2PPlatform', f'{self.name}: no method for logout provided!'))

    def __enter__(self) -> 'P2PPlatform':
        """
        Start of context management protocol.

        Returns:
            Instance of P2PPlatform class

        """
        self.logger.debug(f'Created context manager for {self.name}.')
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
        if self.logged_in:
            if 'logout' in self.urls:
                self.logout_by_url(self.logout_wait_until)
            elif self.logout_locator is not None:
                self.logout_by_button(
                    self.logout_locator,
                    self.logout_wait_until,
                    hover_locator=self.hover_locator)
            else:
                # This should never happen since we already check it in __init__
                msg = f'{self.name}: no method for logout provided!'
                self.logger.error(msg)
                raise RuntimeError(_translate('P2PPlatform', msg))

            self.logged_in = False

        self.signals.disconnect_signals()

        if exc_type:
            raise exc_type(exc_value)

        self.logger.debug(f'Context manager for {self.name} finished.')

    @signals.update_progress
    def log_into_page(
            self, name_field: str, password_field: str,
            credentials: Tuple[str, str], wait_until: expected_conditions,
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
            name_field: Name of web element where the user name has to be
                entered
            password_field: Name of web element where the password has to be
                entered
            credentials: Tuple (username, password) containing login
                credentials
            wait_until: Expected condition in case of successful login
            login_locator: Locator of web element which has to be clicked in
                order to open login form. Default is None.
            fill_delay: Delay in seconds between filling in password and user
                name fields. Default is 0.

        Raises:
            RuntimeError: - If login or password fields cannot be found
                          - If loading the page takes too long

        """
        self.logger.debug(f'Logging into {self.name} website.')
        # Open the login page
        if login_locator is None:
            self.driver.load_url(
                self.urls['login'],
                EC.element_to_be_clickable((By.NAME, name_field)),
                _translate(
                    'P2PPlatform',
                    f'{self.name}: loading the website took too long!'))
        else:
            self.driver.load_url(
                self.urls['login'],
                EC.element_to_be_clickable(login_locator),
                _translate(
                    'P2PPlatform',
                    f'{self.name}: loading the website took too long!'))
            self.driver.click_button(
                login_locator,
                _translate(
                    'P2PPlatform',
                    f'{self.name}: loading the website failed!'),
                wait_until=EC.element_to_be_clickable((By.NAME, name_field)))

        # Enter credentials in name and password field
        try:
            elem = self.driver.wait(
                EC.element_to_be_clickable((By.NAME, name_field)))
            elem.clear()
            elem.send_keys(credentials[0])
            time.sleep(fill_delay)
            elem = self.driver.find_element(By.NAME, password_field)
            elem.clear()
            elem.send_keys(credentials[1])
            time.sleep(fill_delay)
            elem.send_keys(Keys.RETURN)
            self.driver.wait(wait_until)
        except NoSuchElementException:
            self.logger.exception('Login web element not found.')
            raise RuntimeError(_translate(
                'P2PPlatform', '{}: username or password field could not be'
                'found on the login site!').format(self.name))
        except TimeoutException:
            self.logger.exception(
                f'{self.name}: Timeout while filling log in page.')
            raise RuntimeError(_translate(
                'P2PPlatform', '{}: login was not successful. Are the '
                'credentials correct?').format(self.name))

        self.logged_in = True
        self.logger.debug(f'{self.name}: successfully logged in.')

    @signals.update_progress
    def open_account_statement_page(
            self, check_locator: Tuple[str, str]) -> None:
        """
        Open account statement page of the P2P platform.

        This function opens the account statement page of the P2P site.
        The URL of the account statement page is provided as an
        attribute of the P2P class.

        Args:
            check_locator: Locator of a web element which must be present if
                the account statement page loaded successfully

        Raises:
            RuntimeError: - If title of the page does not contain check_title
                          - If loading of page takes too long

        """
        self.logger.debug(f'Open {self.name} account statement page.')
        self.driver.load_url(
            self.urls['statement'],
            EC.presence_of_element_located(check_locator),
            _translate(
                'P2PPlatform',
                f'{self.name}: loading account statement page was not '
                'successful!'))
        self.logger.debug(
            f'{self.name} account statement page opened successfully.')

    @signals.update_progress
    def logout_by_button(
            self, logout_locator: Tuple[str, str],
            wait_until: expected_conditions,
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
        self.logger.debug(f'{self.name}: starting log out by button.')
        self.driver.click_button(
            logout_locator,
            _translate(
                'P2PPlatform', f'{self.name}: logout was not successful!'),
            wait_until=wait_until, hover_locator=hover_locator)
        self.logger.debug(f'{self.name}: log out by button successful.')

    @signals.update_progress
    def logout_by_url(self, wait_until: expected_conditions) -> None:
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
        self.logger.debug(f'{self.name}: starting log out by URL.')
        self.driver.load_url(
            self.urls['logout'], wait_until,
            _translate(
                'P2PPlatform', f'{self.name}: logout was not successful!'))
        self.logger.debug(f'{self.name}: log out by URL successful.')

    @signals.update_progress
    def generate_statement_direct(
            self, date_range: Tuple[date, date],
            start_locator: Tuple[str, str], end_locator: Tuple[str, str],
            date_format: str,
            wait_until: Optional[expected_conditions] = None,
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
            f'{self.name}: starting direct account statement generation for '
            f'date range {date_range}.')
        try:
            date_from = self.driver.find_element(*start_locator)
            date_from.send_keys(Keys.CONTROL + 'a')
            date_from.send_keys(date.strftime(date_range[0], date_format))
            try:
                date_to = self.driver.find_element(*end_locator)
                date_to.click()
                date_to.send_keys(Keys.CONTROL + 'a')
                date_to.send_keys(date.strftime(date_range[1], date_format))

                if submit_btn_locator is None:
                    # If no submit button is provided statement generation can
                    # be started with a simple Enter key click
                    date_to.send_keys(Keys.RETURN)
            except StaleElementReferenceException:
                # Some P2P sites refresh the page after a change
                # which leads to this exception
                # FIXME: treat case when refresh does not work either
                self.logger.exception(
                    f'{self.name}: Date web element stale. Trying to refresh.')
                date_to = self.driver.find_element(*end_locator)
                date_to.send_keys(Keys.CONTROL + 'a')
                date_to.send_keys(date.strftime(date_range[1], date_format))

            if submit_btn_locator is not None:
                submit_btn = self.driver.wait(EC.element_to_be_clickable(
                    submit_btn_locator))
                if self.name == 'Mintos':
                    # Mintos needs some time until the button really works
                    # TODO: find better fix
                    time.sleep(1)
                submit_btn.click()

            # Iuvo needs some time to update the field if there were cash flows
            # TODO: find better fix
            if self.name == 'Iuvo':
                time.sleep(1)

            if wait_until is not None:
                self.driver.wait(wait_until)
        except NoSuchElementException:
            self.logger.exception(f'{self.name}: failed to locate web element.')
            raise RuntimeError(_translate(
                'P2PPlatform',
                f'{self.name}: starting account statement generation failed!'))
        except TimeoutException:
            self.logger.exception(f'{self.name}: Timeout.')
            raise RuntimeError(_translate(
                'P2PPlatform',
                f'{self.name}: account statement generation took too long!'))
        self.logger.debug(
            f'{self.name}: account statement generation successful.')

    @signals.update_progress
    def generate_statement_calendar(
            self, date_range: Tuple[date, date],
            month_locator: Tuple[str, str],
            prev_month_locator: Tuple[str, str],
            day_locator: Tuple[str, str],
            calendar_locator: Tuple[Tuple[str, str], ...],
            wait_until: Optional[expected_conditions] = None,
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
            calendar_locator: Tuple containing locators for the two calendars.
                It must have either length 1 or 2.
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
            f'{self.name}: starting calendar account statement generation for '
            f'date range {date_range}.')
        start_calendar, end_calendar = self._locate_calendars(calendar_locator)

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
                _translate(
                    'P2PPlatform',
                    f'{self.name}: account statement generation failed!'),
                wait_until=wait_until)
        elif wait_until is not None:
            try:
                self.driver.wait(wait_until)
            except TimeoutException:
                self.logger.exception(f'{self.name}: Timeout.')
                raise RuntimeError(_translate(
                    'P2PPlatform',
                    f'{self.name}: account statement generation failed!'))

        self.logger.debug(
            f'{self.name}: account statement generation successful.')

    def _locate_calendars(
            self, calendar_locator: Tuple[Tuple[str, str], ...]) \
            -> Tuple[WebElement, WebElement]:
        """
            Helper method for locating the two calendars for setting account
            statement start and end dates. If calendar_locator contains two
            elements, those are the locators for each calendar. If it contains
            only one element, this is the locator of a datepicker list which
            contains both calendars.

            Args:
                calendar_locator: Tuple containing locators for the two
                    calendars. It must have either length 1 or 2.

            Raises:
                RuntimeError: If the calendars could not be located.

        """
        try:
            if len(calendar_locator) == 2:
                start_calendar = self.driver.find_element(*calendar_locator[0])
                end_calendar = self.driver.find_element(*calendar_locator[1])
            elif len(calendar_locator) == 1:
                datepicker = self.driver.find_elements(*calendar_locator[0])
                start_calendar = datepicker[0]
                end_calendar = datepicker[1]
            else:
                # This should never happen
                self.logger.error(f'Invalid locator: {calendar_locator}.')
                raise RuntimeError(_translate(
                    'P2PPlatform',
                    f'{self.name}: invalid locator for calendar provided!'))
        except NoSuchElementException:
            self.logger.exception(f'{self.name}: failed to locate web element.')
            raise RuntimeError(_translate(
                'P2PPlatform',
                f'{self.name}: starting account statement generation failed!'))

        return start_calendar, end_calendar

    def _set_date_in_calendar(
            self, calendar_: WebElement, target_date,
            month_locator: Tuple[str, str],
            prev_month_locator: Tuple[str, str],
            day_locator: Tuple[str, str],
            day_class_check: Tuple[str, ...] = None) -> None:
        """
        Find and click the given day in the provided calendar.

        Args:
            calendar_: web element which needs to be clicked in order to open
                the calendar
            month_locator: Locator of the web element which contains the name
                of the currently selected month.
            prev_month_locator: Locator of the web element which needs to be
                clicked to switch the calendar to the previous month.
            day_locator: Locator of the table with the days for the given month
            day_class_check: For some websites the days identified by
                day_locator are not unique. They can be further specified by
                providing a tuple of class names in day_class_check.

        Raises:
            RuntimeError: If the target day cannot be found in the calendar.

        """
        self.logger.debug(
            f'{self.name}: setting date {target_date} in calendar.')
        try:
            calendar_.click()
        except ElementClickInterceptedException:
            # Selenium puts the calender field for some web sites under the
            # site header. Scroll site by offset to put it into view again.
            # FIXME: handle case when scrolling is not working either
            self.logger.exception(
                f'{self.name}: trying to recover by scrolling.')
            self.driver.execute_script(f'window.scrollBy(0, -250);')
            calendar_.click()

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
                        f'{self.name}: setting date {target_date} in calendar '
                        f'was successful.')
                    return
        except (NoSuchElementException, TimeoutException):
            self.logger.exception(
                f'{self.name}: failed to set date in calendar.')

        msg = f'{self.name}: could not locate date in calendar!'
        self.logger.error(msg)
        raise RuntimeError(_translate('P2PPlatform', msg))

    @signals.update_progress
    def generate_statement_combo_boxes(
            self, date_dict: Mapping[Tuple[str, str], str],
            submit_btn_locator: Tuple[str, str],
            wait_until: expected_conditions) -> None:
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
            f'{self.name}: starting account statement generation by setting '
            f'combo boxes.')
        try:
            # Change the date values to the given start and end dates
            for locator in date_dict.keys():
                select = Select(self.driver.find_element(*locator))
                select.select_by_visible_text(date_dict[locator])
        except NoSuchElementException:
            self.logger.exception(f'{self.name}: failed to find combo box.')
            raise RuntimeError(_translate(
                'P2PPlatform',
                f'{self.name}: starting account statement generation failed!'))

        # Start the account statement generation
        self.driver.click_button(
            submit_btn_locator,
            _translate(
                'P2PPlatform',
                f'{self.name}: starting account statement generation failed!'),
            wait_until=wait_until)
        self.logger.debug(
            f'{self.name}: account statement generation was successful.')

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
        self.logger.debug(f'{self.name}: starting account statement download.')
        if actions == 'move_to_element':
            hover_locator = download_locator
        else:
            hover_locator = None

        self.driver.click_button(
            download_locator,
            _translate(
                'P2PPlatform',
                f'{self.name}: starting download of account statement '
                f'failed!'),
            hover_locator=hover_locator)

        if not _download_finished(
                statement, self.driver.download_directory):
            raise RuntimeError(_translate(
                'P2PPlatform',
                f'{self.name}: download of account statement failed!'))

        self.logger.debug(f'{self.name}: account statement download finished.')


def _download_finished(
        statement: str, download_directory: str,
        max_wait_time: float = 4.0) -> bool:
    """
    Wait until statement download is done and rename the file to statement.

    Args:
        statement: File name including path where the downloaded file should
            be saved.
        download_directory: Download directory.
        max_wait_time: Maximum time in seconds to wait for download to
            start/finish.

    Returns:
        True if download finished successfully, False if not.

    Raises:
        RuntimeError: If there is more than one file in the download directory.

    """
    done = False
    waiting_time = 0
    download_time = 0

    while not done:
        ongoing_downloads = glob.glob(
            os.path.join(download_directory, '*.crdownload'))
        if ongoing_downloads:
            if download_time > max_wait_time:
                logger.error('Download time exceeded max_wait_time.')
                return False
            time.sleep(1)
            download_time += 1
        else:
            filelist = glob.glob(os.path.join(download_directory, '*'))
            if len(filelist) == 1 and not filelist[0].endswith('crdownload'):
                shutil.move(filelist[0], statement)
                return True

            if len(filelist) > 1:
                # This should never happen since the download directory is a
                # newly created temporary directory
                logger.error(f'More than one active download found: {filelist}')
                raise RuntimeError(_translate(
                    'P2PPlatform',
                    f'Download directory {download_directory} is not empty!'))

            if waiting_time > max_wait_time:
                # If the download didn't start after more than max_wait_time
                # something has gone wrong.
                logger.error('Download did not start within max_wait_time.')
                return False

            time.sleep(1)
            waiting_time += 1

    return False
