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
import os
import shutil
import time
from typing import Mapping, Optional, Tuple, Union

from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, StaleElementReferenceException)
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from PyQt5.QtCore import QCoreApplication

from easyp2p.p2p_signals import Signals
from easyp2p.p2p_webdriver import P2PWebDriver

_translate = QCoreApplication.translate


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
            logout_wait_until: bool,
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

        # Make sure URLs for login and statement page are provided
        if 'login' not in urls:
            raise RuntimeError(_translate(
                'P2PPlatform', '{}: no login URL found!').format(self.name))
        if 'statement' not in urls:
            raise RuntimeError(_translate(
                'P2PPlatform', '{}: no account statement URL found!').format(
                    self.name))

        # Make sure a logout method was provided
        if 'logout' not in self.urls and self.logout_locator is None:
            raise RuntimeError(_translate(
                'P2PPlatform', '{}: no method for logout provided!').format(
                    self.name))

    def __enter__(self) -> 'P2PPlatform':
        """
        Start of context management protocol.

        Returns:
            Instance of P2PPlatform class

        """
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
                raise RuntimeError(_translate(
                    'P2PPlatform',
                    '{}: no method for logout provided!').format(self.name))

            self.logged_in = False
        self.signals.disconnect_signals()
        if exc_type:
            raise exc_type(exc_value)

    @signals.update_progress
    def log_into_page(
            self, name_field: str, password_field: str,
            credentials: Tuple[str, str], wait_until: Union[bool, WebElement],
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
        # Open the login page
        try:
            self.driver.get(self.urls['login'])

            if login_locator is not None:
                login_btn = self.driver.wait(
                    EC.element_to_be_clickable(login_locator))
                login_btn.click()

            # Make sure that the correct URL was loaded
            if self.driver.current_url != self.urls['login']:
                raise RuntimeError(_translate(
                    'P2PPlatform', '{}: loading the website failed!').format(
                        self.name))
        except TimeoutException:
            raise RuntimeError(_translate(
                'P2PPlatform', '{}: loading the website took too long!'.format(
                    self.name)))

        # Enter credentials in name and password field
        try:
            elem = self.driver.wait(
                EC.element_to_be_clickable((By.NAME, name_field)))
            elem.clear()
            elem.send_keys(credentials[0])
            time.sleep(fill_delay)
            elem = self.driver.find_element_by_name(password_field)
            elem.clear()
            elem.send_keys(credentials[1])
            time.sleep(fill_delay)
            elem.send_keys(Keys.RETURN)
            self.driver.wait(wait_until)
        except NoSuchElementException:
            raise RuntimeError(_translate(
                'P2PPlatform', '{}: username or password field could not be'
                'found on the login site!').format(self.name))
        except TimeoutException:
            raise RuntimeError(_translate(
                'P2PPlatform', '{}: login was not successful. Are the '
                'credentials correct?').format(self.name))

        self.logged_in = True

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
        try:
            self.driver.get(self.urls['statement'])
            self.driver.wait(EC.presence_of_element_located(check_locator))
        except TimeoutException:
            raise RuntimeError(_translate(
                'P2PPlatform', '{}: loading account statement page was not '
                'successful!').format(self.name))

    @signals.update_progress
    def logout_by_button(
            self, logout_locator: Tuple[str, str],
            wait_until: Union[bool, WebElement],
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
        try:
            if hover_locator is not None:
                elem = self.driver.find_element(*hover_locator)
                hover = ActionChains(self.driver).move_to_element(elem)
                hover.perform()

            logout_btn = self.driver.wait(
                EC.element_to_be_clickable(logout_locator))
            logout_btn.click()
            self.driver.wait(wait_until)
        except (NoSuchElementException, TimeoutException):
            raise RuntimeWarning(_translate(
                'P2PPlatform', '{}: logout was not successful!').format(
                    self.name))

    @signals.update_progress
    def logout_by_url(self, wait_until: Union[bool, WebElement]) -> None:
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
        try:
            self.driver.get(self.urls['logout'])
            self.driver.wait(wait_until)
        except TimeoutException:
            raise RuntimeWarning(_translate(
                'P2PPlatform', '{}: logout was not successful!').format(
                    self.name))

    @signals.update_progress
    def generate_statement_direct(
            self, date_range: Tuple[date, date],
            start_locator: Tuple[str, str], end_locator: Tuple[str, str],
            date_format: str,
            wait_until: Optional[Union[bool, WebElement]] = None,
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
            raise RuntimeError(_translate(
                'P2PPlatform', '{}: starting account statement generation '
                'failed!').format(self.name))
        except TimeoutException:
            raise RuntimeError(_translate(
                'P2PPlatform', '{}: account statement generation took too '
                'long!').format(self.name))

    @signals.update_progress
    def generate_statement_calendar(
            self, date_range: Tuple[date, date],
            default_dates: Tuple[date, date],
            arrows: Mapping[str, str],
            days_table: Mapping[str, object],
            calendar_locator: Tuple[Tuple[str, str], ...],
            wait_until: Optional[Union[bool, WebElement]] = None,
            submit_btn_locator: Optional[Tuple[str, str]] = None) -> None:
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
            default_dates: Pre-filled default dates of the two date pickers.
            arrows: Dictionary with three entries: class name of left arrows
                (left_arrow_class), class name of right arrows
                (right_arrow_class), tag name of arrows (arrow_tag)
            days_table: Dictionary with four entries:
                class name of day table ('class name'),
                id of day table ('table_id'),
                id of current day ('current_day_id'),
                is day contained in id? ('id_from_calendar')
            calendar_locator: Tuple containing locators for the two calendars.
                It must have either length 1 or 2.
            wait_until: Expected condition in case of successful account
                statement generation. Default is None.
            submit_btn_locator: Locator of button which needs to clicked to
                start account statement generation. Not all P2P platforms
                require this. Default is None.

        Raises:
            RuntimeError: - If a web element cannot be found
                          - If the generation of the account statement
                            takes too long

        """
        try:
            # Identify the two calendars. If calendar_locator contains two
            # elements, those are the locators for each calendar. If it
            # contains only one element, this is the locator of a
            # datepicker list which contains both calendars.
            if len(calendar_locator) == 2:
                start_calendar = self.driver.find_element(*calendar_locator[0])
                end_calendar = self.driver.find_element(*calendar_locator[1])
            elif len(calendar_locator) == 1:
                datepicker = self.driver.find_elements(*calendar_locator[0])
                start_calendar = datepicker[0]
                end_calendar = datepicker[1]
            else:
                # This should never happen
                raise RuntimeError(_translate(
                    'P2PPlatform', '{}: invalid locator for calendar '
                    'provided!').format(self.name))

            # How many clicks on the arrow buttons are necessary?
            start_calendar_clicks = _get_calendar_clicks(
                date_range[0], default_dates[0])
            end_calendar_clicks = _get_calendar_clicks(
                date_range[1], default_dates[1])

            # Identify the arrows for both start and end calendar
            left_arrows = self.driver.find_elements_by_xpath(
                "//{0}[@class='{1}']".format(
                    arrows['arrow_tag'], arrows['left_arrow_class']))
            right_arrows = self.driver.find_elements_by_xpath(
                "//{0}[@class='{1}']".format(
                    arrows['arrow_tag'], arrows['right_arrow_class']))

            # Set start_date
            self._set_date_in_calendar(
                start_calendar, date_range[0].day, start_calendar_clicks,
                left_arrows[0], right_arrows[0], days_table)

            # Set end_date
            self._set_date_in_calendar(
                end_calendar, date_range[1].day, end_calendar_clicks,
                left_arrows[1], right_arrows[1], days_table)

            if submit_btn_locator is not None:
                submit_btn = self.driver.wait(EC.element_to_be_clickable(
                    submit_btn_locator))
                submit_btn.click()

            if wait_until is not None:
                self.driver.wait(wait_until)
        except NoSuchElementException:
            raise RuntimeError(_translate(
                'P2PPlatform', '{}: starting account statement generation '
                'failed!').format(self.name))
        except TimeoutException:
            raise RuntimeError(_translate(
                'P2PPlatform', '{}: account statement generation took too '
                'long!').format(self.name))

    def _set_date_in_calendar(
            self, calendar_: WebElement, day: int, months: int,
            previous_month: WebElement, next_month: WebElement,
            days_table: Mapping[str, object]) -> None:
        """
        Find and click the given day in the provided calendar.

        Args:
            calendar_: web element which needs to be clicked in order to open
                the calendar
            day: day (as int) of the target date
            months: how many months in the past/future (negative/positive) is
                the target date compared to default date
            previous_month: web element which needs to be clicked to switch the
                calendar to the previous month
            next_month: web element which needs to be clicked to switch the
                calendar to the next month
            days_table: Dictionary with four entries:
                class name of day table ('class name'),
                id of day table ('table_id'),
                id of current day ('current_day_id'),
                is day contained in id? ('id_from_calendar')

        """
        # Open the calendar and wait until the buttons for changing the month
        # are visible
        calendar_.click()
        self.driver.wait(EC.visibility_of(previous_month))

        # Switch the calendar to the given target month
        if months < 0:
            for _ in range(0, abs(months)):
                previous_month.click()
        elif months > 0:
            for _ in range(0, months):
                next_month.click()

        # Get table with all days of the selected month
        # If id_from_calendar is True the day number is contained in the id tag
        # Otherwise the days will be identified by the provided class name
        if days_table['id_from_calendar']:
            days_xpath = "//*[@{0}='{1}']//table//td".format(
                days_table['table_id'], calendar_.get_attribute('id'))
        else:
            days_xpath = "//*[@{0}='{1}']//table//td".format(
                days_table['table_id'], days_table['class_name'])
        all_days = self.driver.find_elements_by_xpath(days_xpath)

        # Find and click the target day
        for elem in all_days:
            if days_table['current_day_id'] == '':
                if elem.text == str(day):
                    elem.click()
            else:
                if (elem.text == str(day) and elem.get_attribute('class')
                        == days_table['current_day_id']):
                    elem.click()

    @signals.update_progress
    def generate_statement_combo_boxes(
            self, date_dict: Mapping[Tuple[str, str], str],
            submit_btn_locator: Tuple[str, str],
            wait_until: Union[bool, WebElement]) -> None:
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
        try:
            # Change the date values to the given start and end dates
            for locator in date_dict.keys():
                select = Select(self.driver.find_element(*locator))
                select.select_by_visible_text(date_dict[locator])

            # Start the account statement generation
            submit_btn = self.driver.wait(
                    EC.element_to_be_clickable(submit_btn_locator))
            submit_btn.click()

            # Wait until statement generation is finished
            self.driver.wait(wait_until)
        except NoSuchElementException:
            raise RuntimeError(_translate(
                'P2PPlatform', '{}: starting account statement generation '
                'failed!').format(self.name))
        except TimeoutException:
            raise RuntimeError(_translate(
                'P2PPlatform', '{}: account statement generation took too '
                'long!').format(self.name))

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
            RuntimeError: - If the download button cannot be found
                          - If the downloaded file cannot be found and there
                            is no active download
                          - If more than one active download of
                            default_file_name is found

        """
        try:
            download_button = self.driver.find_element(*download_locator)

            if actions == 'move_to_element':
                action = ActionChains(self.driver)
                action.move_to_element(download_button).perform()

            download_button.click()

            if not _download_finished(
                    statement, self.driver.download_directory):
                raise NoSuchElementException
        except NoSuchElementException:
            raise RuntimeError(_translate(
                'P2PPlatform', '{}: starting download of account statement '
                'failed!').format(self.name))


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
                raise RuntimeError(_translate(
                    'P2PPlatform', 'Download directory {} is not '
                    'empty!').format(download_directory))

            if waiting_time > max_wait_time:
                # If the download didn't start after more than max_wait_time
                # something has gone wrong.
                return False

            time.sleep(1)
            waiting_time += 1

    return False


def _get_calendar_clicks(target_date: date, start_date: date) -> int:
    """
    Get number of clicks necessary to get from start to target month.

    This function will determine how many months in the past/future the
    target date is compared to a given start date. Positive numbers mean
    months into the future, negative numbers months into the past.

    Args:
        target_date: Target date.
        start_date: Start date.

    Returns:
        Number of calendar clicks to get from start to target date.

    """
    if target_date.year != start_date.year:
        clicks = 12 * (target_date.year - start_date.year)
    else:
        clicks = 0

    if target_date.month != start_date.month:
        clicks += target_date.month - start_date.month

    return clicks
