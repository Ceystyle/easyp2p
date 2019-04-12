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
import time
from typing import cast, Mapping, Optional, Sequence, Tuple

from selenium import webdriver
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, StaleElementReferenceException,
    WebDriverException)
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import easyp2p.p2p_helper as p2p_helper


class P2PPlatform:

    """
    Representation of P2P platform including required methods for interaction.

    Represents a P2P platform and the required methods for login/logout,
    generating and downloading account statements.

    """

    def __init__(
            self, name: str, urls: Mapping[str, str],
            statement_file_name: str, logout_wait_until: bool,
            logout_locator: Optional[Tuple[str, str]] = None,
            hover_locator: Optional[Tuple[str, str]] = None) -> None:
        """
        Constructor of P2P class.

        Args:
            name: Name of the P2P platform
            urls: Dictionary with URLs for login page
                (key: 'login'), account statement page (key: 'statement')
                and optionally logout page (key: 'logout')
            logout_wait_until: Expected condition in case
                of successful logout

        Keyword Args:
            logout_locator: Locator of logout web element
            hover_locator: Locator of web element where the
                mouse needs to hover in order to make logout button visible

       Raises:
            RuntimeError: If no URL for login or statement page or no logout
                method is provided

        """
        self.name = name
        self.urls = urls
        self.statement_file_name = statement_file_name
        self.logout_wait_until = logout_wait_until
        self.logout_locator = logout_locator
        self.hover_locator = hover_locator
        self.logged_in = False

        # webdriver will be initialized in __enter__ method to make sure it
        # is always closed again by __exit__
        self.driver = cast(webdriver.Chrome, None)

        # Make sure URLs for login and statement page are provided
        if 'login' not in urls:
            raise RuntimeError(
                '{0}: Keine Login-URL vorhanden!'.format(self.name))
        if 'statement' not in urls:
            raise RuntimeError(
                '{0}: Keine Kontoauszug-URLs für {0} vorhanden!'.format(
                    self.name))

        # Make sure a logout method was provided
        if 'logout' not in self.urls and self.logout_locator is None:
            raise RuntimeError(
                '{0}: Keine Methode für Logout vorhanden!'.format(self.name))

    def __enter__(self) -> 'P2PPlatform':
        """
        Start of context management protocol.

        Returns:
            Instance of P2PPlatform class

        """
        self.init_webdriver()
        return self

    def __exit__(self, exc_type, exc_value, exc_trace) -> None:
        """
        End of context management protocol.

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
                raise RuntimeError(
                    '{0}: Keine Methode für Logout vorhanden!'
                    .format(self.name))

            self.logged_in = False

        self.driver.close()
        if exc_type:
            raise exc_type(exc_value)

    def init_webdriver(self) -> None:
        """
        Initialize Chromedriver as webdriver.

        Initializes Chromedriver as webdriver, sets the download directory
        and opens a new maximized browser window.

        Raises:
            ModuleNotFoundError: If Chromedriver cannot be found

        """
        options = webdriver.ChromeOptions()
#        options.add_argument("--headless")
#        options.add_argument("--window-size=1920,1200")
        prefs = {"download.default_directory": os.path.dirname(
            self.statement_file_name)}
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

    def log_into_page(
            self, name_field: str, password_field: str,
            credentials: Tuple[str, str], wait_until: bool,
            login_locator: Tuple[str, str] = None,
            fill_delay: float = 0.) -> None:
        """
        Log into the P2P platform with using the provided credentials.

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

        Keyword Args:
            login_locator: Locator of web element which has to be clicked in
                order to open login form.
            fill_delay: Delay in seconds between filling in password and user
                name fields

        Raises:
            RuntimeError: - If login or password fields cannot be found
                          - If loading the page takes too long

        """
        # Open the login page
        try:
            self.driver.get(self.urls['login'])

            if login_locator is not None:
                login_btn = self.wdwait(
                    EC.element_to_be_clickable(login_locator))
                login_btn.click()

            # Make sure that the correct URL was loaded
            if self.driver.current_url != self.urls['login']:
                raise RuntimeError(
                    'Die {0}-Webseite konnte nicht geladen werden.'
                    .format(self.name))
        except TimeoutException:
            raise RuntimeError(
                'Das Laden der {0}-Webseite hat zu lange gedauert.'
                .format(self.name))

        # Enter credentials in name and password field
        try:
            elem = self.wdwait(
                EC.element_to_be_clickable((By.NAME, name_field)))
            elem.clear()
            elem.send_keys(credentials[0])
            time.sleep(fill_delay)
            elem = self.driver.find_element_by_name(password_field)
            elem.clear()
            elem.send_keys(credentials[1])
            elem.send_keys(Keys.RETURN)
            # Login currently takes a long time for Twino, thus increase the
            # waiting time for now. They promised an web site update for
            # 28/01/2018 which should fix this issue.
            if self.name == 'Twino':
                self.wdwait(wait_until, delay=10)
            else:
                self.wdwait(wait_until)
        except NoSuchElementException:
            raise RuntimeError(
                'Benutzername/Passwort-Felder konnten nicht auf der '
                '{0}-Loginseite gefunden werden!'.format(self.name))
        except TimeoutException:
            raise RuntimeError(
                '{0}-Login war leider nicht erfolgreich. Passwort korrekt?'
                .format(self.name))

        self.driver.logged_in = True

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
            # TODO: catch error if url cannot be loaded
            self.driver.get(self.urls['statement'])
            self.wdwait(EC.presence_of_element_located(check_locator))
        except TimeoutException:
            raise RuntimeError(
                '{0}-Kontoauszugsseite konnte nicht geladen werden!'
                .format(self.name))

    def logout_by_button(
            self, logout_locator: Tuple[str, str],
            wait_until: bool,
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

        Keyword Args:
            hover_locator: Locator of web element over which the mouse
                needs to hover in order to make the logout button visible

        Raises:
            RuntimeWarning: - If loading of page takes too long
                            - If the download button cannot be found

        """
        try:
            if hover_locator is not None:
                elem = self.driver.find_element(*hover_locator)
                hover = ActionChains(self.driver).move_to_element(elem)
                hover.perform()

            logout_btn = self.wdwait(
                EC.element_to_be_clickable(logout_locator))
            logout_btn.click()
            self.wdwait(wait_until)
        except (NoSuchElementException, TimeoutException):
            raise RuntimeWarning(
                '{0}-Logout war nicht erfolgreich!'.format(self.name))

    def logout_by_url(self, wait_until: bool) -> None:
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
            self.wdwait(wait_until)
        except TimeoutException:
            raise RuntimeWarning(
                '{0}-Logout war nicht erfolgreich!'.format(self.name))

    def generate_statement_direct(
            self, date_range: Tuple[date, date],
            start_locator: Tuple[str, str], end_locator: Tuple[str, str],
            date_format: str, wait_until: bool = None,
            submit_btn_locator: Tuple[str, str] = None) -> None:
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
            end_element: Locator of web element where the end date needs to be
                entered.
            date_format: Date format which the platform uses

        Keyword Args:
            wait_until: Expected condition in case of successful account
                statement generation
            submit_btn_locator: Locator of button which needs to clicked to
                start account statement generation. Not all P2P platforms
                require this.

        Raises:
            RuntimeError: - If a web element cannot be found
                          - If the generation of the account statement
                            takes too long

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
                date_to.send_keys(Keys.RETURN)
            except StaleElementReferenceException:
                # Some P2P sites refresh the page after a change
                # which leads to this exception
                date_to = self.driver.find_element(*end_locator)
                date_to.send_keys(Keys.CONTROL + 'a')
                date_to.send_keys(date.strftime(date_range[1], date_format))

            if submit_btn_locator is not None:
                submit_btn = self.wdwait(EC.element_to_be_clickable(
                    submit_btn_locator))
                if self.name == 'Mintos':
                    # Mintos needs some time until the button really works
                    # TODO: find better fix
                    time.sleep(1)
                submit_btn.click()

            # Iuvo needs some time to update the field if there were cashflows
            # TODO: find better fix
            if self.name == 'Iuvo':
                time.sleep(1)

            if wait_until is not None:
                self.wdwait(wait_until)
        except NoSuchElementException:
            raise RuntimeError(
                'Generierung des {0}-Kontoauszugs konnte nicht gestartet '
                'werden.'.format(self.name))
        except TimeoutException:
            raise RuntimeError(
                'Generierung des {0}-Kontoauszugs hat zu lange gedauert.'
                .format(self.name))

    def generate_statement_calendar(
            self, date_range: Tuple[date, date],
            default_dates: Tuple[date, date],
            arrows: Mapping[str, str],
            days_table: Mapping[str, object],
            calendar_locator: Tuple[Tuple[str, str], ...]) -> None:
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
                account statement must be generated
            default_dates: Pre-filled default dates of the two date pickers
            arrows: Dictionary with three entries: class name of left arrows
                (left_arrow_class), class name of right arrows
                (right_arrow_class), tag name of arrows (arrow_tag)
            days_table: Dictionary with four entries:
                class name of day table ('class name'),
                id of day table ('table_id'),
                id of current day ('current_day_id'),
                is day contained in id? ('id_from_calendar')
            calendar_locator: Tuple containing locators for the two calendars.
                It must have either length 1 or 2

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
                raise RuntimeError(
                    '{0}: Ungültiger Locator für Kalender übergeben'
                    .format(self.name))

            # How many clicks on the arrow buttons are necessary?
            start_calendar_clicks = p2p_helper.get_calendar_clicks(
                date_range[0], default_dates[0])
            end_calendar_clicks = p2p_helper.get_calendar_clicks(
                date_range[1], default_dates[1])

            # Identify the arrows for both start and end calendar
            left_arrows = self.driver.find_elements_by_xpath(
                "//{0}[@class='{1}']".format(
                    arrows['arrow_tag'], arrows['left_arrow_class']))
            right_arrows = self.driver.find_elements_by_xpath(
                "//{0}[@class='{1}']".format(
                    arrows['arrow_tag'], arrows['right_arrow_class']))

            # Set start_date
            self.set_date_in_calendar(
                start_calendar, date_range[0].day, start_calendar_clicks,
                left_arrows[0], right_arrows[0], days_table)

            # Set end_date
            self.set_date_in_calendar(
                end_calendar, date_range[1].day, end_calendar_clicks,
                left_arrows[1], right_arrows[1], days_table)

        except NoSuchElementException:
            raise RuntimeError(
                'Generierung des {0}-Kontoauszugs konnte nicht gestartet '
                'werden.'.format(self.name))
        except TimeoutException:
            raise RuntimeError(
                'Generierung des {0}-Kontoauszugs hat zu lange gedauert.'
                .format(self.name))

    def set_date_in_calendar(
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
        self.wdwait(EC.visibility_of(previous_month))

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

    def download_statement(
            self, download_locator: Tuple[str, str], actions=None) -> None:
        """
        Download account statement file by clicking the provided button.

        Downloads the generated account statement by clicking the provided
        download button. Some P2P sites require further actions before the
        button is clickable, which can be provided by the optional actions
        variable. The method also checks if the download was successful.
        If true, the _rename_statement method is called to rename the
        downloaded file to self.statement_file_name.

        Args:
            download_locator: Locator of the download button

        Keyword Args:
            actions: 'move to element' or None: some P2P sites require that the
                mouse hovers over the download button to make it clickable

        Raises:
            RuntimeError: - If the download button cannot be found
                          - If the downloaded file cannot be found and there
                            is no active download
                          - If more than one active download of
                            default_file_name is found

        """
        # Get a list of all files in the download directory
        dl_dir = os.path.dirname(self.statement_file_name)
        file_list = glob.glob(os.path.join(dl_dir, '*'))

        # Find and click the download button
        try:
            download_button = self.driver.find_element(*download_locator)

            if actions == 'move_to_element':
                action = ActionChains(self.driver)
                action.move_to_element(download_button).perform()

            download_button.click()
        except NoSuchElementException:
            raise RuntimeError(
                'Download des {0}-Kontoauszugs konnte nicht gestartet werden.'
                .format(self.name))

        # Wait until download has finished
        file_name = self._wait_for_download_end(file_list, dl_dir)

        # Rename downloaded file
        self._rename_statement(file_name, self.statement_file_name)

    def _rename_statement(
            self, source_file_name: str, target_file_name: str) -> None:
        """
        Rename downloaded statement from source_file_name to target_file_name.

        Args:
            source_file_name: file name including path of the file which should
                be renamed
            target_file_name: file name including path which the file should be
                renamed to

        Raises:
            RuntimeError: If source file cannot be found

        """
        error_msg = (
            '{0}-Kontoauszug konnte nicht im Downloadverzeichnis gefunden '
            'werden.'.format(self.name))

        try:
            os.rename(source_file_name, target_file_name)
        except FileNotFoundError:
            raise RuntimeError(error_msg)

    def _wait_for_download_end(
            self, file_list: Sequence[str], dl_dir: str,
            max_waiting_time: float = 4.0) -> str:
        """
        Wait until download has finished and return name of downloaded file.

        Args:
            file_list: List of all files in the download directory before the
                download started
            dl_dir: Download directory

        Keyword Args:
            max_waiting_time: If there is no active or finished download after
                max_waiting_time something has gone wrong

        Returns:
            Name including path of the downloaded file

        Raises:
            RuntimeError: - If the downloaded file cannot be found and there
                            is no active download
                          - If more than one active download of
                            default_file_name is found

        """
        _download_finished = False
        _waiting_time = 0
        while not _download_finished:
            new_file_list = glob.glob(os.path.join(dl_dir, '*'))
            if len(new_file_list) - len(file_list) == 1:
                _download_finished = True
            elif new_file_list == file_list:
                # TODO: make sure that there were no leftover downloads from
                # a failed run in the past
                ongoing_downloads = glob.glob(os.path.join(
                    dl_dir, '*.crdownload'))
                if not ongoing_downloads and _waiting_time > max_waiting_time:
                    # If the download didn't start after more than
                    # max_waiting_time something has gone wrong.
                    raise RuntimeError(
                        'Download des {0}-Kontoauszugs wurde abgebrochen!'
                        .format(self.name))

                time.sleep(1)
                _waiting_time += 1
            else:
                # This should never happen
                raise RuntimeError(
                    'Mehr als ein aktiver Download des {0}-Kontoauszugs '
                    'gefunden!'.format(self.name))

        file_name = [file for file in new_file_list if file not in file_list][0]
        return file_name

    def wdwait(self, wait_until: bool, delay: float = 5.0) -> WebElement:
        """
        Shorthand for WebDriverWait.

        Args:
            wait_until: Expected condition for which the webdriver should wait

        Keyword Args:
            delay: Maximal waiting time in seconds

        Returns:
            WebElement which WebDriverWait waited for.

        """
        return WebDriverWait(self.driver, delay).until(wait_until)
