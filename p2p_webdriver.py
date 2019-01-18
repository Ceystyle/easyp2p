# -*- coding: utf-8 -*-
# Copyright 2018-19 Niko Sandschneider

"""
p2p_webdriver contains the main code for handling the P2P platforms.

This module defines the P2P class and contains code for accessing and handling
supported P2P sites. It relies mainly on functionality provided by the Selenium
webdriver. easyP2P uses Chromedriver as webdriver.

.. moduleauthor:: Niko Sandschneider <nsandschn@gmx.de>

"""

import calendar
from datetime import datetime, date, timedelta
import glob
import os
import time
from typing import Mapping, Sequence, Tuple, Union

import pandas as pd
import requests
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.action_chains import ActionChains

ExpectedCondition = Union[
    EC.element_to_be_clickable('locator'),
    EC.presence_of_element_located('locator'),
    EC.text_to_be_present_in_element('locator', str), EC.title_contains(str),
    EC.visibility_of('locator')]

OpenSelenium = Union[
    'open_selenium_bondora', 'open_selenium_dofinance',
    'open_selenium_estateguru', 'open_selenium_grupeer',
    'open_selenium_iuvo', 'open_selenium_mintos',
    'open_selenium_peerberry', 'open_selenium_robocash',
    'open_selenium_swaper', 'open_selenium_twino']

class P2P:

    """
    Representation of P2P platform including required methods for interaction.

    Represents a P2P platform and the required methods for login/logout,
    generating and downloading account statements.

    """

    def __init__(
            self, name: str, urls: Mapping[str, str], *logout_args,
            default_file_name: str = None, file_format: str = None,
            **logout_kwargs) -> None:
        """
        Constructor of P2P class.

        Args:
            name (str): Name of the P2P platform
            urls (dict[str, str]): Dictionary with URLs for login page
                (key: 'login'), account statement page (key: 'statement')
                and optionally logout page (key: 'logout')
            logout_args: further arguments for the logout method

        Keyword Args:
            default_file_name (str): default name for account statement
                downloads, chosen by the P2P platform
            file_format (str): format of the download file
            logout_kwargs: keyword arguments for the logout method

        """
        self.name = name
        self.urls = urls
        self.default_file_name = default_file_name
        self.file_format = file_format
        self.logout_args = logout_args
        self.logout_kwargs = logout_kwargs
        self.delay = 5  # delay in seconds, input for WebDriverWait
        self.driver = None

        # Make sure URLs for login and statement page are provided
        if 'login' not in urls:
            raise RuntimeError('Keine Login-URL für {0} '
                               'vorhanden!'.format(self.name))
        if 'statement' not in urls:
            raise RuntimeError('Keine Kontoauszug-URLs für {0} '
                               'vorhanden!'.format(self.name))

    def __enter__(self) -> 'P2P':
        """
        Start of context management protocol.

        Returns:
            P2P: instance of P2P class

        """
        self.init_webdriver()
        return self

    def __exit__(self, exc_type, exc_value, exc_trace) -> None:
        """End of context management protocol."""
        if 'logout' in self.urls:
            self.logout_by_url(*self.logout_args)
        else:
            try:
                self.logout_by_button(*self.logout_args, **self.logout_kwargs)
            except NoSuchElementException:
                # If an error occurs before login, the logout button is not
                # present yet, which leads to this error. It can be ignored.
                pass
        self.driver.close()
        if exc_type:
            raise exc_type(exc_value)

    def init_webdriver(self) -> None:
        """
        Initialize Chromedriver as webdriver.

        This function initializes Chromedriver as webdriver, sets the
        default download location to p2p_downloads relative to the current
        working directory and opens a new maximized browser window.

        """
        # TODO: handle error cases
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--window-size=1920,1200")
        dl_location = os.path.join(os.getcwd(), 'p2p_downloads')
        prefs = {"download.default_directory": dl_location}
        options.add_experimental_option("prefs", prefs)
        driver = webdriver.Chrome(options=options)
        driver.maximize_window()
        self.driver = driver

    def open_start_page(
            self, wait_until: ExpectedCondition,
            title_check: str = None) -> bool:
        """
        Open start page of P2P platform.

        This function will open the login/start page of the P2P platform
        in the webdriver. It will check the title of the window to make
        sure the page was loaded correctly.

        Args:
            wait_until (ExpectedCondition): Expected condition in case of
                success, in general the clickability of the user name field.

        Keyword Args:
            title_check (str): used to check if the correct page was loaded.
                Defaults to name of P2P platform if None is provided.

        Returns:
            bool: True on success, False on failure.

        Throws:
            RuntimeError: if the expected web page title is not found or if
                loading the page takes too long

        """
        # Most platforms use their name in the title
        # title_check will handle the few cases where they don't
        if title_check is None:
            title_check = self.name

        try:
            self.driver.get(self.urls['login'])
            self.wdwait(wait_until)
            # Additional check that the correct page was loaded
            if title_check not in self.driver.title:
                raise RuntimeError(
                    'Die {0} Webseite konnte nicht geladen werden.'
                    ''.format(self.name))
        except TimeoutException:
            raise RuntimeError(
                'Das Laden der {0} Webseite hat zu lange gedauert.'
                ''.format(self.name))

        return True

    def log_into_page(
            self, name_field: str, password_field: str,
            credentials: Tuple[str, str], wait_until: ExpectedCondition,
            login_field: str = None, find_login_by: str = By.XPATH,
            fill_delay: float = 0) -> bool:
        """
        Log into the P2P platform with provided user name/password.

        This function performs the login procedure for the P2P site.
        It fills in user name and password. Some P2P sites only show
        the user name and password field after clicking a button.
        The id of the button can be provided by the optional login_field.
        Some P2P sites (e.g. Swaper) also require a small delay
        between filling in name and password. Otherwise it can
        sometimes happen that the password is mistakenly written
        to the name field, too.

        Args:
            name_field (str): name of web element where the user name
                has to be entered.
            password_field (str): name of web element where the password
                has to be entered.
            credentials (tuple[str, str]): login information: (username,
                password)
            wait_until (ExpectedCondition): Expected condition in case of
                success.

        Keyword Args:
            login_field (str): id of web element which has to be clicked
                in order to open login form.
            find_login_by (str): attribute of By class for translating
                login_field into web element.
            fill_delay (float): a small delay between filling in password
                and user name fields.

        Returns:
            bool: True on success, False on failure.

        Throws:
            RuntimeError: - if login or password fields cannot be found
                          - if loading the page takes too long

        """
        try:
            if login_field is not None:
                self.driver.find_element(find_login_by, login_field).click()

            self.wdwait(EC.element_to_be_clickable((By.NAME, name_field)))
            elem = self.driver.find_element_by_name(name_field)
            elem.clear()
            elem.send_keys(credentials[0])
            time.sleep(fill_delay)
            elem = self.driver.find_element_by_name(password_field)
            elem.clear()
            elem.send_keys(credentials[1])
            elem.send_keys(Keys.RETURN)
            self.wdwait(wait_until)
        except NoSuchElementException:
            raise RuntimeError(
                'Benutzername/Passwort-Felder konnten nicht auf der '
                '{0}-Loginseite gefunden werden!'.format(self.name))
        except TimeoutException:
            raise RuntimeError(
                '{0}-Login war leider nicht erfolgreich. Passwort korrekt?'
                ''.format(self.name))

        return True

    def open_account_statement_page(
            self, title: str, element_to_check: str,
            check_by: str = By.ID) -> bool:
        """
        Open account statement page of the P2P platform.

        This function opens the account statement page of the P2P site.
        The URL of the account statement page is provided as an
        attribute of the P2P class.

        Args:
            title (str): (part of the) window title of the account statement
                page.
            element_to_check (str): id of web element which must be present
                on the account statement page.

        Keyword Args:
            check_by (str): attribute of By class for translating
                element_to_check into web element.

        Returns:
            bool: True on success, False on failure.

        Throws:
            RuntimeError: - if title of the page is not equal to provided one
                          - if loading of page takes too long

        """
        try:
            self.driver.get(self.urls['statement'])
            self.wdwait(EC.presence_of_element_located(
                (check_by, element_to_check)))
            assert title in self.driver.title
        except (AssertionError, TimeoutException):
            raise RuntimeError(
                '{0}-Kontoauszugsseite konnte nicht geladen werden!'
                ''.format(self.name))

        return True

    def logout_by_button(
            self, logout_elem: str, logout_elem_by: str,
            wait_until: ExpectedCondition, hover_elem: str = None,
            hover_elem_by: str = None) -> None:
        """
        Logout of P2P platform using the provided logout button.

        This function performs the logout procedure for P2P sites
        where a button needs to be clicked to logout. For some sites the
        button only becomes clickable after hovering over a certain element.
        This element is provided by the optional hover_elem variable.

        Args:
            logout_elem (str): id of logout button.
            logout_elem_by (str): attribute of By class for translating
                logout_elem into web element.
            wait_until (ExpectedCondition): Expected condition in case of
                successful logout.

        Keyword Args:
            hover_elem (str): id of web element over which the mouse needs
                to be hovered in order to make the logout button visible.
            hover_elem_by (str): attribute of By class for translating
                hover_elem into web element.

        Throws:
            RuntimeError: if loading of page takes too long

        """
        try:
            if hover_elem is not None:
                elem = self.driver.find_element(hover_elem_by, hover_elem)
                hover = ActionChains(self.driver).move_to_element(elem)
                hover.perform()
                self.wdwait(EC.element_to_be_clickable(
                    (logout_elem_by, logout_elem)))

            self.driver.find_element(logout_elem_by, logout_elem).click()
            self.wdwait(wait_until)
        except TimeoutException:
            raise RuntimeWarning(
                '{0}-Logout war nicht erfolgreich!'.format(self.name))
            # Continue anyway

    def logout_by_url(
            self, wait_until: ExpectedCondition) -> None:
        """
        Logout of P2P platform using the provided URL.

        This function performs the logout procedure for P2P sites
        where the logout page can by accessed by URL. The URL itself is
        provided in the urls dict attribute of the P2P class.

        Args:
            wait_until (ExpectedCondition): Expected condition in case of
                successful logout

        Throws:
            RuntimeError: if loading of page takes too long

        """
        try:
            self.driver.get(self.urls['logout'])
            self.wdwait(wait_until)
        except TimeoutException:
            raise RuntimeWarning(
                '{0}-Logout war nicht erfolgreich!'.format(self.name))
            # Continue anyway

    def generate_statement_direct(
            self, start_date: datetime.date, end_date: datetime.date,
            start_element: str, end_element: str, date_format: str,
            find_elem_by: str = By.ID, wait_until: ExpectedCondition = None,
            submit_btn: str = None, find_submit_btn_by: str = None) -> bool:
        """
        Generate acc. statement for platforms where date fields can be edited.

        For P2P sites where the two date range fields for account statement
        generation can be edited directly. The function will locate the two
        date fields, enter start and end date and then start the account
        statement generation.

        Args:
            start_date (datetime.date): start of date range for which the
                account statement should be generated.
            end_date (datetime.date): end of date range for which the
                account statement should be generated.
            start_element (str): id of field where the start date needs
                to be entered.
            end_element (str): id of field where the end date needs
                to be entered.
            date_format (str): date format.

        Keyword Args:
            find_elem_by (str): attribute of By class for translating
                start_element and end_element into web elements.
            wait_until (ExpectedCondition): Expected condition in case of
                successful account statement generation.
            submit_btn (str): id of button which needs to clicked to start
                account statement generation. Not all P2P require this.
            find_submit_btn_by (str): attribute of By class for translating
                submit_btn into web element.

        Returns:
            bool: True on success, False on failure.

        """
        try:
            date_from = self.driver.find_element(find_elem_by, start_element)
            date_from.send_keys(Keys.CONTROL + 'a')
            date_from.send_keys(datetime.strftime(start_date, date_format))

            try:
                date_to = self.driver.find_element(find_elem_by, end_element)
                date_to.click()
                date_to.send_keys(Keys.CONTROL + 'a')
                date_to.send_keys(datetime.strftime(end_date, date_format))
                date_to.send_keys(Keys.RETURN)
            except StaleElementReferenceException:
                # Some P2P sites refresh the page after a change
                # which leads to this exception
                date_to = self.driver.find_element(find_elem_by, end_element)
                date_to.send_keys(Keys.CONTROL + 'a')
                date_to.send_keys(datetime.strftime(end_date, date_format))

            if submit_btn is not None:
                button = self.wdwait(EC.element_to_be_clickable(
                    (find_submit_btn_by, submit_btn)))
                if self.name == 'Mintos':
                    # Mintos needs some time until the button really works
                    # TODO: find better fix
                    time.sleep(1)
                button.click()

            if wait_until is not None:
                self.wdwait(wait_until)
        except NoSuchElementException:
            raise RuntimeError('Generierung des {0}-Kontoauszugs konnte nicht '
                               'gestartet werden.'.format(self.name))
        except TimeoutException:
            raise RuntimeError('Generierung des {0}-Kontoauszugs hat zu lange '
                               'gedauert.'.format(self.name))

        return True

    def generate_statement_calendar(
            self, start_date: datetime.date, end_date: datetime.date,
            default_dates: Sequence[datetime.date], arrows: Mapping[str, str],
            days_table: Mapping[str, Union[str, bool]],
            calendar_id_by: str, calendar_id: str) -> bool:
        """
        Generate account statement by clicking days in a calendar.

        For P2P sites where the two date range fields for account
        statement generation cannot be edited directly, but must be
        clicked in a calendar. The function will locate the two calendars,
        determine how many clicks are necessary to get to the
        correct month, perform the clicks and finally locate and click
        the chosen day.

        Args:
            start_date (datetime.date): start of date range for which the
                account statement should be generated.
            end_date (datetime.date): end of date range for which the
                account statement should be generated.
            default_dates (list[datetime.datetime]): the two pre-filled
                default dates of the date pickers.
            arrows (dict[str, str]): dictionary with three entries: class name
                of left arrows, class name of right arrows,
                tag name of arrows.
            days_table (dict[str, {str, bool}]): dictionary with four entries:
                class name of day table, id of day table, id of current day,
                is day contained in id?.
            calendar_id_by (str): attribute of By class for translating
                calendar_id to web element.
            calendar_id (str): id of the two calendars.

        Returns:
            bool: True on success, False on failure.

        """
        try:
            # Identify the two calendars
            if calendar_id_by == 'name':
                start_calendar = self.driver.find_element_by_name(
                    calendar_id[0])
                end_calendar = self.driver.find_element_by_name(
                    calendar_id[1])
            elif calendar_id_by == 'class':
                datepicker = self.driver.find_elements_by_xpath(
                    "//div[@class='{0}']".format(calendar_id))
                start_calendar = datepicker[0]
                end_calendar = datepicker[1]
            else:
                # This should never happen
                raise RuntimeError(
                    '{0}: Keine ID für Kalender übergeben'.format(self.name))

            # How many clicks on the arrow buttons are necessary?
            start_calendar_clicks = get_calendar_clicks(
                start_date, default_dates[0])
            end_calendar_clicks = get_calendar_clicks(
                end_date, default_dates[1])

            # Identify the arrows for both start and end calendar
            left_arrows = self.driver.find_elements_by_xpath(
                "//{0}[@class='{1}']".format(
                    arrows['arrow_tag'], arrows['left_arrow_class']))
            right_arrows = self.driver.find_elements_by_xpath(
                "//{0}[@class='{1}']".format(
                    arrows['arrow_tag'], arrows['right_arrow_class']))

            # Set start_date
            self.set_date_in_calendar(
                start_calendar, start_date.day, start_calendar_clicks,
                left_arrows[0], right_arrows[0], days_table)

            # Set end_date
            self.set_date_in_calendar(
                end_calendar, end_date.day, end_calendar_clicks,
                left_arrows[1], right_arrows[1], days_table)

        except NoSuchElementException:
            raise RuntimeError('Generierung des {0}-Kontoauszugs konnte nicht '
                               'gestartet werden.'.format(self.name))
        except TimeoutException:
            raise RuntimeError('Generierung des {0}-Kontoauszugs hat zu lange '
                               'gedauert.'.format(self.name))

        return True

    def set_date_in_calendar(
            self, calendar_: WebElement, day: int, months: int,
            previous_month: WebElement, next_month: WebElement,
            days_table: Mapping[str, Union[str, bool]]) -> None:
        """
        Find and click the given day in the provided calendar.

        Args:
            calendar_ (WebElement): web element which needs to be clicked
                in order to open the calendar
            day (int): day number of the target date
            months (int): how many months in the past/future
                (negative/positive) is the target date
            previous_month (WebElement): web element to switch calendar to the
                previous month
            next_month (WebElement): web element to switch calendar to the
                next month
            days_table (dict[str, {str, bool}]): dictionary with four entries:
                class name of day table, id of day table, id of current day,
                is day contained in id?.

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
            self, download_btn: str, find_btn_by: str, actions=None) -> bool:
        """
        Download account statement by clicking the provided button.

        Downloads the generated account statement and checks
        if the download was successful. If the download was successful,
        it will also call the rename_statement function to rename
        the downloaded file to the file name chosen by the user.

        Args:
            download_btn (str): id of the download button.
            find_btn_by (str): attribute of By class for translating
                download_btn into web element.

        Keyword Args:
            actions (str): 'move to element' or None: some P2P sites
                require that the mouse hovers over a certain element
                in order to make the download button clickable.

        Returns:
            bool: True on success, False on failure.

        """
        try:
            download_button = self.driver.find_element(
                find_btn_by, download_btn)

            if actions == 'move_to_element':
                action = ActionChains(self.driver)
                action.move_to_element(download_button).perform()
            download_button.click()
        except NoSuchElementException:
            raise RuntimeError(
                'Download des {0} Kontoauszugs konnte nicht gestartet werden.'
                ''.format(self.name))

        download_finished = False
        duration = 0
        while not download_finished:
            file_list = glob.glob(
                'p2p_downloads/{0}.{1}'.format(
                    self.default_file_name, self.file_format))
            if len(file_list) == 1:
                download_finished = True
            elif len(file_list) == 0:
                file_list = glob.glob(
                    'p2p_downloads/{0}.{1}.crdownload'.format(
                        self.default_file_name, self.file_format))
                if len(file_list) < 1 and duration > 1:
                    # Duration ensures that at least one second has gone by
                    # since starting the download
                    raise RuntimeError(
                        'Download des {0} Kontoauszugs abgebrochen.'
                        ''.format(self.name))
                elif duration < 1:
                    time.sleep(1)
                    duration += 1

        if not self.rename_statement():
            return False

        return True

    def wdwait(self, wait_until: ExpectedCondition) -> WebElement:
        """
        Shorthand for WebDriverWait.

        Args:
            wait_until (ExpectedCondition): expected condition for which the
                webdriver should wait.

        Returns:
            WebElement: WebElement which WebDriverWait waited for.

        """
        return WebDriverWait(self.driver, self.delay).until(wait_until)

    def clean_download_location(self) -> bool:
        """
        Ensure that there are no old download files in download location.

        Makes sure that the download location does not contain
        old downloads. In case old downloads are detected they will be
        automatically removed. The user is informed via a warning message.

        Returns:
            bool: True if download location is clean, False if user needs to
                  manually delete the files.

        Throws:
            RuntimeError: if old download files with the same default name
                          cannot be deleted.

        """
        file_list = glob.glob(
            'p2p_downloads/{0}.{1}'.format(
                self.default_file_name, self.file_format))
        if len(file_list) > 0:
            for file in file_list:
                try:
                    os.remove(file)
                except:
                    raise RuntimeError('Alte {0}-Downloads in ./p2p_downloads '
                                       'konnten nicht gelöscht werden. Bitte '
                                       'manuell entfernen!'.format(self.name))

            raise RuntimeWarning('Alte {0}-Downloads in ./p2p_downloads wurden'
                                 'entfernt.'.format(self.name))

        return True

    def rename_statement(self) -> bool:
        """
        Rename downloaded statement to platform_name_statement.file_format.

        Will rename the downloaded statement from the
        default name chosen by the P2P platform to
        platform_name_statement.file_format.

        Returns:
            bool: True on success, False on failure.

        Throws:
            RuntimeError: if the downloaded statement cannot be found

        """
        file_list = glob.glob('p2p_downloads/{0}.{1}'.format(
            self.default_file_name, self.file_format))
        if len(file_list) == 1:
            os.rename(
                file_list[0], 'p2p_downloads/{0}_statement.{1}'.format(
                    self.name.lower(), self.file_format))
        elif len(file_list) == 0:
            raise RuntimeError(
                '{0}-Kontoauszug konnte nicht im Downloadverzeichnis gefunden '
                'werden.'.format(self.name))
        else:
            # This should never happen
            raise RuntimeError('Alte {0} Downloads in ./p2p_downloads '
                               'entdeckt. Bitte zuerst entfernen.'
                               ''.format(self.name))

        return True

def get_calendar_clicks(
        target_date: datetime.date, start_date: datetime.date) -> int:
    """
    Get number of calendar clicks necessary to get from start to target month.

    This function will determine how many months in the
    past/future the target date is compared to a given
    start date. Positive numbers mean months into the
    future, negative numbers months into the past.

    Args:
        target_date (datetime.date): Target date.
        start_date (datetime.date): Start date.

    Returns:
        int: number of months between start and
            target date.

    """
    if target_date.year != start_date.year:
        clicks = 12 * (target_date.year - start_date.year)
    else:
        clicks = 0

    if target_date.month != start_date.month:
        clicks += target_date.month - start_date.month

    return clicks

def get_list_of_months(
        start_date: datetime.date, end_date: datetime.date) -> list:
    """
    Get list of months between (including) start and end date.

    Args:
        start_date (datetime.date): start date
        end_date (datetime.date): end_date

    Returns:
        list (datetime.date): List of months
    """
    months = []
    m = start_date
    while m < end_date:
        start_of_month = date(m.year, m.month, 1)
        end_of_month = date(m.year, m.month, calendar.monthrange(
            m.year, m.month)[1])
        months.append([start_of_month, end_of_month])
        m = m + timedelta(days=31)

    return months

def short_month_to_nbr(short_name: str) -> str:
    """
    Helper method for translating month short names to numbers.

    Returns:
        str: two-digit month number padded with 0

    """
    map_short_month_to_nbr = {
        'Jan': '01', 'Feb': '02', 'Mrz': '03', 'Mar': '03',
        'Apr': '04', 'Mai': '05', 'May': '05', 'Jun': '06', 'Jul': '07',
        'Aug': '08', 'Sep': '09', 'Okt': '10', 'Oct': '10', 'Nov': '11',
        'Dez': '12', 'Dec': '12'}

    return map_short_month_to_nbr[short_name]

def nbr_to_short_month(nbr: str) -> str:
    """
    Helper method for translating numbers to month short names.

    Returns:
        str: month short name

    """
    # Only German locale is used so far
    map_nbr_to_short_month = {
        '01': 'Jan', '02': 'Feb', '03': 'Mrz', '04': 'Apr', '05': 'Mai',
        '06': 'Jun', '07': 'Jul', '08': 'Aug', '09': 'Sep', '10': 'Okt',
        '11': 'Nov', '12': 'Dez'}

    return map_nbr_to_short_month[nbr]

def open_selenium_bondora(
        start_date: datetime.date, end_date: datetime.date,
        credentials: Tuple[str, str]) -> bool:
    """
    Generate and download the Bondora account statement for given date range.

    Args:
        start_date (datetime.date): Start of date range for which account
            statement must be generated.
        end_date (datetime.date): End of date range for which account
            statement must be generated.
        credentials (tuple[str, str]): (username, password) for Bondora

    Returns:
        bool: True on success, False on failure

    """
    urls = {
        'login': 'https://www.bondora.com/de/login',
        'logout': 'https://www.bondora.com/de/authorize/logout',
        'statement': 'https://www.bondora.com/de/cashflow'}
    xpaths = {
        'search_btn': ('//*[@id="page-content-wrapper"]/div/div/div[1]/form/'
                       'div[3]/button'),
        'start_date': ('/html/body/div[1]/div/div/div/div[3]/div/table/tbody/'
                       'tr[2]/td[1]/a')}

    with P2P('Bondora', urls, EC.title_contains('Einloggen')) as bondora:

        driver = bondora.driver

        if not bondora.open_start_page(
                EC.element_to_be_clickable((By.NAME, 'Email'))):
            return False

        if not bondora.log_into_page(
                'Email', 'Password', credentials,
                EC.element_to_be_clickable((By.LINK_TEXT, 'Cashflow'))):
            return False

        if not bondora.open_account_statement_page(
                title='Cashflow', element_to_check='StartYear'):
            return False

        start_year = Select(
            driver.find_element_by_id('StartYear')).first_selected_option.text
        start_month = Select(
            driver.find_element_by_id('StartMonth')).first_selected_option.text
        end_year = Select(
            driver.find_element_by_id('EndYear')).first_selected_option.text
        end_month = Select(
            driver.find_element_by_id('EndMonth')).first_selected_option.text

        if start_year != start_date.year:
            select = Select(driver.find_element_by_id('StartYear'))
            select.select_by_visible_text(str(start_date.year))

        if short_month_to_nbr(start_month) != start_date.strftime('%m'):
            select = Select(driver.find_element_by_id('StartMonth'))
            select.select_by_visible_text(nbr_to_short_month(
                start_date.strftime('%m')))

        if end_year != end_date.year:
            select = Select(driver.find_element_by_id('EndYear'))
            select.select_by_visible_text(str(end_date.year))

        if short_month_to_nbr(end_month) != end_date.strftime('%m'):
            select = Select(driver.find_element_by_id('EndMonth'))
            select.select_by_visible_text(nbr_to_short_month(
                end_date.strftime('%m')))

        driver.find_element_by_xpath(xpaths['search_btn']).click()
        bondora.wdwait(
            EC.text_to_be_present_in_element(
                (By.XPATH, xpaths['start_date']),
                '{0} {1}'.format(start_date.strftime('%b'), start_date.year)))

        cashflow_table = driver.find_element_by_id('cashflow-content')
        df = pd.read_html(
            cashflow_table.get_attribute("innerHTML"), index_col=0,
            thousands='.', decimal=',')
        df[0].to_csv('p2p_downloads/bondora_statement.csv')

    return True

def open_selenium_mintos(
        start_date: datetime.date, end_date: datetime.date,
        credentials: Tuple[str, str]) -> bool:
    """
    Generate and download the Mintos account statement for given date range.

    Args:
        start_date (datetime.date): Start of date range for which
            account statement must be generated.
        end_date (datetime.date): End of date range for which
            account statement must be generated.
        credentials (tuple[str, str]): (username, password) for Mintos

    Returns:
        bool: True on success, False on failure.

    """
    urls = {
        'login': 'https://www.mintos.com/de/',
        'statement': 'https://www.mintos.com/de/kontoauszug/'}
    xpaths = {
        'logout_btn': "//a[contains(@href,'logout')]"}
    today = datetime.today()
    default_file_name = '{0}{1}{2}-account-statement'.format(
        today.year, today.strftime('%m'), today.strftime('%d'))

    with P2P(
            'Mintos', urls, xpaths['logout_btn'],
            By.XPATH, EC.title_contains('Vielen Dank'),
            default_file_name=default_file_name, file_format='xlsx') as mintos:

        if not mintos.clean_download_location():
            return False

        if not mintos.open_start_page(
                EC.element_to_be_clickable((By.NAME, 'MyAccountButton'))):
            return False

        if not mintos.log_into_page(
                '_username', '_password', credentials,
                EC.element_to_be_clickable((By.LINK_TEXT, 'Kontoauszug')),
                login_field='MyAccountButton', find_login_by=By.NAME):
            return False

        if not mintos.open_account_statement_page(
                'Account Statement', 'period-from'):
            return False

        if not mintos.generate_statement_direct(
                start_date, end_date, 'period-from', 'period-to', '%d.%m.%Y',
                wait_until=EC.presence_of_element_located(
                    (By.ID, 'export-button')),
                submit_btn='filter-button', find_submit_btn_by=By.ID):
            return False

        success = mintos.download_statement('export-button', By.ID)

    return success

def open_selenium_robocash(
        start_date: datetime.date, end_date: datetime.date,
        credentials: Tuple[str, str]) -> bool:
    """
    Generate and download the Robocash account statement for given date range.

    Args:
        start_date (datetime.date): Start of date range for which account
            statement must be generated.
        end_date (datetime.date): End of date range for which account
            statement must be generated.
        credentials (tuple[str, str]): (username, password) for Robocash

    Returns:
        bool: True on success, False on failure

    Throws:
        RuntimeError: - if the statement button cannot be found
                      - if the download of the statement takes too long

    """
    urls = {
        'login': 'https://robo.cash/de',
        'logout': 'https://robo.cash/de/logout',
        'statement': 'https://robo.cash/de/cabinet/statement'}
    xpaths = {
        'login_check': '/html/body/header/div/div/div[2]/nav/ul/li[3]/a',
        'login_field': '/html/body/header/div/div/div[3]/a[1]',
        'start_page_check': '/html/body/header/div/div/div[3]/a[1]'}

    with P2P('Robocash', urls, EC.title_contains('Willkommen')) as robocash:

        if not robocash.open_start_page(
                EC.presence_of_element_located(
                    (By.XPATH, xpaths['start_page_check'])),
                'Robo.cash'):
            return False

        if not robocash.log_into_page(
                'email', 'password', credentials,
                EC.element_to_be_clickable((By.XPATH, xpaths['login_check'])),
                login_field=xpaths['login_field']):
            return False

        if not robocash.open_account_statement_page(
                title='Kontoauszug', element_to_check='new_statement'):
            return False

        try:
            robocash.driver.find_element_by_id('new_statement').click()
        except NoSuchElementException:
            raise RuntimeError(
                'Generierung des Robocash-Kontoauszugs konnte nicht gestartet '
                'werden.')

        if not robocash.generate_statement_direct(
                start_date, end_date, 'date-after', 'date-before', '%Y-%m-%d'):
            return False

        # Robocash does not automatically show download button after statement
        # generation is done. An explicit reload of the page is needed.
        present = False
        wait = 0
        while not present:
            try:
                robocash.driver.get(robocash.urls['statement'])
                robocash.wdwait(
                    EC.element_to_be_clickable((By.ID, 'download_statement')))
                present = True
            except TimeoutException:
                wait += 1
                if wait > 10:  # Roughly 10*delay=30 seconds
                    raise RuntimeError(
                        'Generierung des Robocash-Kontoauszugs hat zu lange '
                        'gedauert!')

        # Robocash creates the download names randomly, therefore the default
        # name is not known like for the other P2P sites. Thus we don't use the
        # download button, but the download URL to get the statement.
        download_url = robocash.driver.find_element_by_id(
            'download_statement').get_attribute('href')
        driver_cookies = robocash.driver.get_cookies()
        cookies_copy = {}
        for driver_cookie in driver_cookies:
            cookies_copy[driver_cookie["name"]] = driver_cookie["value"]
        r = requests.get(download_url, cookies=cookies_copy)
        with open('p2p_downloads/robocash_statement.xls', 'wb') as output:
            output.write(r.content)

    return True

def open_selenium_swaper(
        start_date: datetime.date, end_date: datetime.date,
        credentials: Tuple[str, str]) -> bool:
    """
    Generate and download the Swaper account statement for given date range.

    Args:
        start_date (datetime.date): Start of date range for which account
            statement must be generated.
        end_date (datetime.date): End of date range for which account
            statement must be generated.
        credentials (tuple[str, str]): (username, password) for Swaper

    Returns:
        bool: True on success, False on failure

    """
    urls = {
        'login': 'https://www.swaper.com/#/dashboard',
        'statement': 'https://www.swaper.com/#/overview/account-statement'}
    xpaths = {
        'download_btn': ('//*[@id="account-statement"]/div[3]/div[4]/div/'
                         'div[1]/a/div[1]/div/span[2]'),
        'logout_btn': '//*[@id="logout"]/span[1]/span'}

    with P2P(
            'Swaper', urls, xpaths['logout_btn'], By.XPATH,
            EC.presence_of_element_located((By.ID, 'about')),
            default_file_name='excel-storage*', file_format='xlsx') as swaper:

        if not swaper.clean_download_location():
            return False

        if not swaper.open_start_page(
                EC.presence_of_element_located((By.NAME, 'email'))):
            return False

        if not swaper.log_into_page(
                'email', 'password', credentials,
                EC.presence_of_element_located((By.ID, 'open-investments')),
                fill_delay=0.5):
            return False

        if not swaper.open_account_statement_page(
                title='Swaper', element_to_check='account-statement'):
            return False

        calendar_id_by = 'class'
        calendar_id = 'datepicker-container'
        arrows = {'arrow_tag': 'div',
                  'left_arrow_class': 'icon icon icon-left',
                  'right_arrow_class': 'icon icon icon-right'}
        days_table = {'class_name': '',
                      'current_day_id': ' ',
                      'id_from_calendar': True,
                      'table_id': 'id'}
        default_dates = [datetime.today().replace(day=1), datetime.now()]

        if not swaper.generate_statement_calendar(
                start_date, end_date, default_dates, arrows, days_table,
                calendar_id_by, calendar_id):
            return False

        success = swaper.download_statement(xpaths['download_btn'], By.XPATH)

    return success

def open_selenium_peerberry(
        start_date: datetime.date, end_date: datetime.date,
        credentials: Tuple[str, str]) -> bool:
    """
    Generate and download the PeerBerry account statement for given date range.

    Args:
        start_date (datetime.date): Start of date range for which account
            statement must be generated.
        end_date (datetime.date): End of date range for which account
            statement must be generated.
        credentials (tuple[str, str]): (username, password) for PeerBerry

    Returns:
        bool: True on success, False on failure

    """
    urls = {
        'login': 'https://peerberry.com/de/login',
        'statement': 'https://peerberry.com/de/statement'}
    xpaths = {
        'cookie_policy': '//*[@id="app"]/div/div/div/div[4]/div/div/div[1]',
        'download_btn': ('//*[@id="app"]/div/div/div/div[2]/div/div[2]/div[3]/'
                         'div[2]/div'),
        'logout_btn': ('//*[@id="app"]/div/div/div/div[1]/div[1]/div/div/'
                       'div[2]/div'),
        'start_balance': ('/html/body/div[1]/div/div/div/div[2]/div/div[2]/'
                          'div[2]/div/div/div[1]'),
        'statement_btn': ('/html/body/div[1]/div/div/div/div[2]/div/div[2]/'
                          'div[1]/div/div[2]/div/div[2]/div/span')}

    with P2P(
            'PeerBerry', urls, xpaths['logout_btn'], By.XPATH,
            EC.title_contains('Einloggen'),
            default_file_name='transactions', file_format='csv') as peerberry:

        if not peerberry.clean_download_location():
            return False

        if not peerberry.open_start_page(
                EC.element_to_be_clickable(
                    (By.NAME, 'email')), 'PeerBerry.com'):
            return False

        if not peerberry.log_into_page(
                'email', 'password', credentials,
                EC.element_to_be_clickable((By.LINK_TEXT, 'Kontoauszug'))):
            return False

        if not peerberry.open_account_statement_page(
                'Kontoauszug', 'startDate', check_by=By.NAME):
            return False

        # Close the cookie policy, if present
        try:
            peerberry.driver.find_element_by_xpath(
                xpaths['cookie_policy']).click()
        except NoSuchElementException:
            pass

        # Create account statement for given date range
        default_dates = [datetime.now(), datetime.now()]
        arrows = {'arrow_tag': 'th',
                  'left_arrow_class': 'rdtPrev',
                  'right_arrow_class': 'rdtNext'}
        calendar_id_by = 'name'
        calendar_id = ['startDate', 'endDate']
        days_table = {'class_name': 'rdtDays',
                      'current_day_id': 'rdtDay',
                      'id_from_calendar': False,
                      'table_id': 'class'}

        if not peerberry.generate_statement_calendar(
                start_date, end_date, default_dates, arrows, days_table,
                calendar_id_by, calendar_id):
            return True

        # After setting the dates, the statement button needs to be clicked in
        # order to actually generate the statement
        try:
            peerberry.driver.find_element_by_xpath(
                xpaths['statement_btn']).click()
            peerberry.wdwait(
                EC.text_to_be_present_in_element(
                    ((By.XPATH, xpaths['start_balance'])),
                    'Eröffnungssaldo '+str(start_date).format('%Y-%m-%d')))
        except NoSuchElementException:
            raise RuntimeError('Generierung des {0}-Kontoauszugs konnte nicht '
                               'gestartet werden.'.format(peerberry.name))
        except TimeoutException:
            raise RuntimeError('Generierung des {0}-Kontoauszugs hat zu lange '
                               'gedauert.'.format(peerberry.name))

        success = peerberry.download_statement(
            xpaths['download_btn'], By.XPATH, actions='move_to_element')

    return success

def open_selenium_estateguru(
        start_date: datetime.date, end_date: datetime.date,
        credentials: Tuple[str, str]) -> bool:
    """
    Generate and download Estateguru account statement for given date range.

    Args:
        start_date (datetime.date): Start of date range for which account
            statement must be generated, is not used for Estateguru.
        end_date (datetime.date): End of date range for which account
            statement must be generated, is not used for Estateguru.
        credentials (tuple[str, str]): (username, password) for Estateguru

    Returns:
        bool: True on success, False on failure

    """
    urls = {
        'login': 'https://estateguru.co/portal/login/auth?lang=de',
        'logout': 'https://estateguru.co/portal/logout/index',
        'statement': 'https://estateguru.co/portal/portfolio/account'}
    xpaths = {
        'account_statement_check': ('/html/body/section/div/div/div/div[2]/'
                                    'section[1]/div/div/div[2]/div/form/'
                                    'div[2]/ul/li[5]/a'),
        'select_btn': ('/html/body/section/div/div/div/div[2]/section[2]/'
                       'div[1]/div[2]/button')}
    today = datetime.today()
    default_file_name = 'payments_{0}-{1}-{2}*'.format(today.year,
                                                       today.strftime('%m'),
                                                       today.strftime('%d'))
    with P2P(
            'Estateguru', urls, EC.title_contains('Einloggen/Registrieren'),
            default_file_name=default_file_name,
            file_format='csv') as estateguru:

        if not estateguru.open_start_page(
                EC.element_to_be_clickable((By.NAME, 'username')),
                'Sign in/Register'):
            return False

        if not estateguru.log_into_page(
                'username', 'password', credentials,
                EC.element_to_be_clickable((By.LINK_TEXT, 'KONTOSTAND'))):
            return -1

        if not estateguru.open_account_statement_page(
                'Übersicht', xpaths['account_statement_check'], By.XPATH):
            return False

        # Estateguru does not provide functionality for filtering payment
        # dates. Therefore we download the statement which includes all
        # cashflows ever generated for this account.
        estateguru.driver.find_element_by_xpath(xpaths['select_btn']).click()
        estateguru.wdwait(EC.element_to_be_clickable((By.LINK_TEXT, 'CSV')))
        estateguru.download_statement('CSV', By.LINK_TEXT)

    return True

def open_selenium_iuvo(
        start_date: datetime.date, end_date: datetime.date,
        credentials: Tuple[str, str]) -> bool:
    """
    Generate and download the Iuvo account statement for given date range.

    Args:
        start_date (datetime.date): Start of date range for which account
            statement must be generated.
        end_date (datetime.date): End of date range for which account
            statement must be generated.
        credentials (tuple[str, str]): (username, password) for Iuvo

    Returns:
        bool: True on success, False on failure

    """
    urls = {
        'login': 'https://www.iuvo-group.com/de/login/',
        'statement': 'https://www.iuvo-group.com/de/account-statement/'}
    xpaths = {
        'start_balance_name': ('/html/body/div[5]/main/div/div/div/div[4]/div/'
                               'table/thead/tr[1]/td[1]/strong'),
        'start_balance_value': ('/html/body/div[5]/main/div/div/div/div[4]/'
                                'div/table/thead/tr[1]/td[2]/strong')}
    with P2P(
            'Iuvo', urls, 'p2p_logout', By.ID,
            EC.title_contains('Investieren Sie in Kredite'),
            hover_elem='User name', hover_elem_by=By.LINK_TEXT) as iuvo:

        driver = iuvo.driver

        if not iuvo.open_start_page(
                EC.element_to_be_clickable((By.NAME, 'login'))):
            return False

        if not iuvo.log_into_page(
                'login', 'password', credentials,
                EC.element_to_be_clickable(
                    (By.ID, 'p2p_btn_deposit_page_add_funds'))):
            return False

        # Click away cookie policy, if present
        try:
            driver.find_element_by_id(
                'CybotCookiebotDialogBodyButtonAccept').click()
        except NoSuchElementException:
            pass

        if not iuvo.open_account_statement_page('Kontoauszug', 'date_from'):
            return False

        # Since Dec 2018 Iuvo only provides aggregated cashflows
        # for the whole requested date range, no more detailed information
        # Workaround to get monthly data: create account statement for
        # each month in date range

        # Get all required monthly date ranges
        months = get_list_of_months(start_date, end_date)

        df_result = None

        for month in months:
            start_balance = driver.find_element_by_xpath(
                xpaths['start_balance_value']).text

            if not iuvo.generate_statement_direct(
                    month[0], month[1], 'date_from', 'date_to', '%Y-%m-%d',
                    wait_until=EC.text_to_be_present_in_element(
                        (By.XPATH, xpaths['start_balance_name']),
                        'Anfangsbestand'),
                    submit_btn='account_statement_filters_btn',
                    find_submit_btn_by=By.ID):
                return False

            # Read statement from page
            new_start_balance = driver.find_element_by_xpath(
                xpaths['start_balance_value']).text
            if new_start_balance == start_balance:
                # If the start balance didn't change, the calculation is most
                # likely not finished yet
                # TODO: find better way to wait until new statement is
                # generated
                time.sleep(3)
            statement_table = driver.find_element_by_class_name(
                'table-responsive')
            df = pd.read_html(
                statement_table.get_attribute("innerHTML"), index_col=0)[0]
            df = df.T
            df['Datum'] = month[0].strftime('%d.%m.%Y')

            if df_result is None:
                df_result = df
            else:
                df_result = df_result.append(df, sort=True)

        df_result.to_csv('p2p_downloads/iuvo_statement.csv')

    return True

def open_selenium_grupeer(
        start_date: datetime.date, end_date: datetime.date,
        credentials) -> bool:
    """
    Generate and download the Grupeer account statement for given date range.

    Args:
        start_date (datetime.date): Start of date range for which account
            statement must be generated.
        end_date (datetime.date): End of date range for which account
            statement must be generated.

    Returns:
        bool: True on success, False on failure

    """
    urls = {
        'login': 'https://www.grupeer.com/de/login',
        'statement': 'https://www.grupeer.com/de/account-statement'}
    xpaths = {
        'logout_btn': ('/html/body/div[4]/header/div/div/div[2]/div[1]/'
                       'div/div/ul/li/a/span')}
    with P2P(
            'Grupeer', urls, 'Ausloggen', By.LINK_TEXT,
            EC.title_contains('P2P Investitionsplattform Grupeer'),
            xpaths['logout_btn'], By.XPATH,
            default_file_name='Account statement',
            file_format='xlsx') as grupeer:

        if not grupeer.clean_download_location():
            return False

        if not grupeer.open_start_page(
                EC.element_to_be_clickable((By.NAME, 'email'))):
            return False

        if not grupeer.log_into_page(
                'email', 'password', credentials,
                EC.element_to_be_clickable(
                    (By.LINK_TEXT, 'Meine Investments'))):
            return False

        if not grupeer.open_account_statement_page(
                'Account Statement', 'from'):
            return False

        if not grupeer.generate_statement_direct(
                start_date, end_date, 'from', 'to', '%d.%m.%Y',
                wait_until=EC.text_to_be_present_in_element(
                    (By.CLASS_NAME, 'balance-block'),
                    'Bilanz geöffnet am '
                    + str(start_date.strftime('%d.%m.%Y'))),
                submit_btn='submit', find_submit_btn_by=By.NAME):
            return False

        success = grupeer.download_statement('excel', By.NAME)

    return success

def open_selenium_dofinance(
        start_date: datetime.date, end_date: datetime.date,
        credentials: Tuple[str, str]) -> bool:
    """
    Generate and download the Dofinance account statement for given date range.

    Args:
        start_date (datetime.date): Start of date range for which account
            statement must be generated.
        end_date (datetime.date): End of date range for which account
            statement must be generated.
        credentials (tuple[str, str]): (username, password) for DoFinance

    Returns:
        bool: True on success, False on failure

    """
    urls = {
        'login': 'https://www.dofinance.eu/de/users/login',
        'logout': 'https://www.dofinance.eu/de/users/logout',
        'statement': 'https://www.dofinance.eu/de/users/statement'}
    default_file_name = 'Statement_{0} 00_00_00-{1} 23_59_59'.format(
        start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
    with P2P(
            'DoFinance', urls, EC.title_contains('Kreditvergabe Plattform'),
            default_file_name=default_file_name,
            file_format='xlsx') as dofinance:

        if not dofinance.clean_download_location():
            return False

        if not dofinance.open_start_page(
                EC.element_to_be_clickable((By.NAME, 'email')),
                title_check='Anmeldung'):
            return False

        if not dofinance.log_into_page(
                'email', 'password', credentials,
                EC.element_to_be_clickable((By.LINK_TEXT, 'TRANSAKTIONEN'))):
            return False

        if not dofinance.open_account_statement_page(
                'Transaktionen', 'date-from'):
            return False

        if not dofinance.generate_statement_direct(
                start_date, end_date, 'date-from', 'date-to', '%d.%m.%Y',
                wait_until=EC.element_to_be_clickable((By.NAME, 'xls'))):
            return False

        success = dofinance.download_statement('xls', By.NAME)

    return success

def open_selenium_twino(
        start_date: datetime.date, end_date: datetime.date,
        credentials: Tuple[str, str]) -> bool:
    """
    Generate and download the Twino account statement for given date range.

    Args:
        start_date (datetime.date): Start of date range for which account
            statement must be generated.
        end_date (datetime.date): End of date range for which account
            statement must be generated.
        credentials (tuple[str, str]): (username, password) for Twino

    Returns:
        bool: True on success, False on failure

    """
    urls = {
        'login': 'https://www.twino.eu/de/',
        'statement': ('https://www.twino.eu/de/profile/investor/'
                      'my-investments/account-transactions')}
    xpaths = {
        'end_date': '//*[@date-picker="filterData.processingDateTo"]',
        'login_btn': ('/html/body/div[1]/div[2]/div[1]/header[1]/div/nav/div/'
                      'div[1]/button'),
        'logout_btn': '//a[@href="/logout"]',
        'start_date': '//*[@date-picker="filterData.processingDateFrom"]',
        'statement': ('//a[@href="/de/profile/investor/my-investments/'
                      'individual-investments"]')}

    with P2P(
            'Twino', urls, xpaths['logout_btn'], By.XPATH,
            EC.element_to_be_clickable((By.XPATH, xpaths['login_btn'])),
            default_file_name='account_statement_*',
            file_format='xlsx') as twino:

        if not twino.clean_download_location():
            return False

        if not twino.open_start_page(
                EC.element_to_be_clickable((By.XPATH, xpaths['login_btn'])),
                title_check='TWINO'):
            return False

        if not twino.log_into_page(
                'email', 'login-password', credentials,
                EC.element_to_be_clickable((By.XPATH, xpaths['statement'])),
                login_field=xpaths['login_btn'], find_login_by=By.XPATH):
            return False

        if not twino.open_account_statement_page(
                'TWINO', xpaths['start_date'], check_by=By.XPATH):
            return False

        if not twino.generate_statement_direct(
                start_date, end_date, xpaths['start_date'], xpaths['end_date'],
                '%d.%m.%Y', find_elem_by=By.XPATH,
                wait_until=EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, '.accStatement__pdf'))):
            return False

        success = twino.download_statement(
            '.accStatement__pdf', By.CSS_SELECTOR)

    return success
