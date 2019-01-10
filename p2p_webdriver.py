# -*- coding: utf-8 -*-

"""
p2p_webdriver.

    This module defines the P2P class and contains code for accessing and
    handling supported P2P sites. It relies mainly on functionality provided
    by the Selenium webdriver. easyP2P uses Chromedriver as webdriver.

.. moduleauthor:: Niko Sandschneider <nsandschn@gmx.de>

"""

import calendar
import credentials
from datetime import datetime,  date,  timedelta
import glob
import os
import pandas as pd
import requests
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.action_chains import ActionChains
import time


class P2P:

    """
    Represents a P2P platform and the required methods for login/logout,
    generating and downloading account statements.
    """

    def __init__(
            self,  name, login_url, statement_url,
            default_file_name=None, file_format=None,
            logout_url=None):
        """
        Constructor

        Args:
            name (str): Name of the P2P platform
            login_url (str): Login URL of the P2P platform
            statement_url (str): URL of the account statement page of the
                P2P platform

        Keyword Args:
            default_file_name (str): default name for account statement
                downloads, chosen by the P2P platform
            file_format (str): format of the download file
            logout_url (str): Logout URL of the P2P platform

        """
        self.name = name
        self.login_url = login_url
        self.statement_url = statement_url
        self.default_file_name = default_file_name
        self.file_format = file_format
        self.logout_url = logout_url
        self.delay = 5  # delay in seconds, input for WebDriverWait
        self.init_webdriver()

    def init_webdriver(self):
        """
        This function initializes Chromedriver as webdriver, sets the
        default download location to p2p_downloads relative to the current
        working directory and opens a new maximized browser window.

        """
        # TODO. handle error cases
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--window-size=1920,1200")
        dl_location = os.path.join(os.getcwd(), 'p2p_downloads')
        prefs = {"download.default_directory": dl_location}
        options.add_experimental_option("prefs", prefs)
        driver = webdriver.Chrome(options=options)
        driver.maximize_window()
        self.driver = driver

    def open_start_page(self, wait_until, title_check=None):
        """
        This function will open the login/start page of the P2P platform
        in the webdriver. It will check the title of the window to make
        sure the page was loaded correctly.

        Args:
            wait_until (EC.*): Expected condition in case of success,
                in general the clickability of the user name field.

        Keyword Args:
            title_check (str): used to check if the correct page was loaded.
                Defaults to name of P2P platform if None is provided.

        Returns:
            int: 0 on success, -1 on failure.

        """
        # Most platforms use their name in the title
        # title_check will handle the few cases where they don't
        if title_check is None:
            title_check = self.name

        try:
            self.driver.get(self.login_url)
            self.wdwait(wait_until)
            # Additional check that the correct page was loaded
            if title_check not in self.driver.title:
                raise RuntimeError(
                    'Die {0} Webseite konnte nicht geladen werden.'
                    ''.format(self.name))
                return -1
        except TimeoutException:
            raise RuntimeError(
                'Das Laden der {0} Webseite hat zu lange gedauert.'
                ''.format(self.name))
            return -1

        return 0

    def log_into_page(
            self, name_field, password_field, wait_until,
            login_field=None, find_login_by=By.XPATH, fill_delay=0):
        """
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
            wait_until (EC.*): Expected condition in case of success.

        Keyword Args:
            login_field (str): id of web element which has to be clicked
                in order to open login form.
            find_login_by (By.*): method for translating login_field into
                web element.
            fill_delay (float): a small delay between filling in password
                and user name fields.

        Returns:
            int: 0 on success, -1 on failure.

        """
        try:
            getattr(credentials, self.name)['username']
            getattr(credentials, self.name)['password']
        except AttributeError:
            raise RuntimeError(
                'Username/Passwort für {0} sind nicht vorhanden. Bitte '
                'manuell zu credentials.py hinzufügen'.format(self.name))
            return -1

        try:
            if login_field is not None:
                self.driver.find_element(find_login_by, login_field).click()

            self.wdwait(EC.element_to_be_clickable((By.NAME, name_field)))
            elem = self.driver.find_element_by_name(name_field)
            elem.clear()
            elem.send_keys(getattr(credentials, self.name)['username'])
            time.sleep(fill_delay)
            elem = self.driver.find_element_by_name(password_field)
            elem.clear()
            elem.send_keys(getattr(credentials, self.name)['password'])
            elem.send_keys(Keys.RETURN)
            self.wdwait(wait_until)
        except NoSuchElementException:
            raise RuntimeError(
                'Benutzername/Passwort-Felder konnten nicht auf der '
                '{0}-Loginseite gefunden werden!'.format(self.name))
            return -1
        except TimeoutException:
            raise RuntimeError(
                '{0}-Login war leider nicht erfolgreich. Passwort korrekt?'
                ''.format(self.name))
            return -1

        return 0

    def open_account_statement_page(
            self, title, element_to_check, check_by=By.ID):
        """
        This function opens the account statement page of the P2P site.
        The URL of the account statement page is provided as an
        attribute of the P2P class.

        Args:
            title (str): (part of the) window title of the account statement
                page.
            element_to_check (str): id of web element which must be present
                on the account statement page.

        Keyword Args:
            check_by (By.*): method for translating element_to_check into
                web element.

        Returns:
            int: 0 on success, -1 on failure.

        """
        try:
            self.driver.get(self.statement_url)
            self.wdwait(EC.presence_of_element_located(
                (check_by, element_to_check)))
            assert title in self.driver.title
        except (AssertionError,  TimeoutException):
            raise RuntimeError(
                '{0}-Kontoauszugsseite konnte nicht geladen werden!'
                ''.format(self.name))
            return -1

        return 0

    def logout_by_button(
            self, logout_elem,  logout_elem_by, wait_until,
            hover_elem=None, hover_elem_by=None):
        """
        This function performs the logout procedure for P2P sites
        where a button needs to be clicked to logout. For some sites the
        button only becomes clickable after hovering over a certain element.
        This element is provided by the optional hover_elem variable.

        Args:
            logout_elem (str): id of logout button.
            logout_elem_by (By.*): method for translating logout_elem into
                web element.
            wait_until (EC.*): Expected condition in case of successful logout.

        Keyword Args:
            hover_elem (str): id of web element over which the mouse needs
                to be hovered in order to make the logout button visible.
            hover_elem_by (By.*): method for translating hover_elem into
                web element.

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

    def logout_by_url(self, wait_until):
        """
        This function performs the logout procedure for P2P sites
        where the logout page has an URL. The URL itself is provided
        as an attribute of the P2P class.

        Args:
            wait_until (EC.*): Expected condition in case of successful logout
        """
        try:
            self.driver.get(self.logout_url)
            self.wdwait(wait_until)
        except TimeoutException:
            raise RuntimeWarning(
                '{0}-Logout war nicht erfolgreich!'.format(self.name))
            # Continue anyway

    def generate_statement_direct(
            self, start_date, end_date,
            start_element, end_element, date_format,
            find_elem_by=By.ID, wait_until=None,
            submit_btn=None, find_submit_btn_by=None):
        """
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
            find_elem_by (By.*): method for translating start_element and
                end_element into web elements.
            wait_until (EC.*): Expected condition in case of successful
                account statement generation.
            submit_btn (str): id of button which needs to clicked to start
                account statement generation. Not all P2P require this.
            find_submit_btn_by (By.*): method for translating submit_btn
                into web element.

        Returns:
            int: 0 on success, -1 on failure.
        """
        try:
            date_from = self.driver.find_element(find_elem_by, start_element)
            date_from.send_keys(Keys.CONTROL + 'a')
            date_from.send_keys(datetime.strftime(start_date, date_format))

            try:
                date_to = self.driver.find_element(find_elem_by,  end_element)
                date_to.click()
                date_to.send_keys(Keys.CONTROL + 'a')
                date_to.send_keys(datetime.strftime(end_date, date_format))
                date_to.send_keys(Keys.RETURN)
            except StaleElementReferenceException:
                # Some P2P sites refresh the page after a change
                # which leads to this exception
                date_to = self.driver.find_element(find_elem_by,  end_element)
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
            return -1
        except TimeoutException:
            raise RuntimeError('Generierung des {0}-Kontoauszugs hat zu lange '
                'gedauert.'.format(self.name))
            return -1

        return 0

    def generate_statement_calendar(
            self, start_date, end_date,
            default_dates, arrows, days_table,
            calendar_id_by, calendar_id):
        """
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
            default_dates (list of datetime.datetime): the two pre-filled
                default dates of the date pickers.
            arrows (list (str, str, str)): list with three entries: class name
                of left arrows, class name of right arrows,
                tag name of arrows.
            days_table (list (str, str, str, bool)): list with four entries:
                class name of day table, id of day table, id of current day,
                is day contained in id?.
            calendar_id_by (str): method for translating calendar_id
                to web element.
            calendar_id (str): id of the two calendars.

        Returns:
            int: 0 on success, -1 on failure.
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
                return -1

            # How many clicks on the arrow buttons are necessary?
            start_calendar_clicks = get_calendar_clicks(
                start_date,  default_dates[0])
            end_calendar_clicks = get_calendar_clicks(
                end_date,  default_dates[1])

            # Identify the arrows for both start and end calendar
            left_arrows = self.driver.find_elements_by_xpath(
                "//{0}[@class='{1}']".format(arrows[2], arrows[0]))
            right_arrows = self.driver.find_elements_by_xpath(
                "//{0}[@class='{1}']".format(arrows[2], arrows[1]))

            # Set start_date
            start_calendar.click()
            self.wdwait(EC.visibility_of(left_arrows[0]))
            if start_calendar_clicks < 0:
                for _ in range(0, abs(start_calendar_clicks)):
                    left_arrows[0].click()
            elif start_calendar_clicks > 0:
                for _ in range(0, start_calendar_clicks):
                    right_arrows[0].click()

            # Get all dates from left calendar and find the start day
            day_table_class_name = days_table[0]
            day_table_identifier = days_table[1]
            current_day_identifier = days_table[2]
            id_from_calendar = days_table[3]

            if id_from_calendar:
                start_days_xpath = "//*[@{0}='{1}']//table//td".format(
                    day_table_identifier, start_calendar.get_attribute('id'))
            else:
                start_days_xpath = "//*[@{0}='{1}']//table//td".format(
                    day_table_identifier, day_table_class_name)
            all_days = self.driver.find_elements_by_xpath(start_days_xpath)

            for elem in all_days:
                if current_day_identifier == '':
                    if elem.text == str(start_date.day):
                        elem.click()
                else:
                    if (elem.text == str(start_date.day)
                            and elem.get_attribute('class')
                            == current_day_identifier):
                        elem.click()

            # Set end_date
            end_calendar.click()
            self.wdwait(EC.visibility_of(left_arrows[1]))
            if end_calendar_clicks < 0:
                for _ in range(0, abs(end_calendar_clicks)):
                    left_arrows[1].click()
            elif end_calendar_clicks > 0:
                for _ in range(0, end_calendar_clicks):
                    right_arrows[1].click()

            # Get all dates from right calendar and find the end day
            if id_from_calendar:
                end_days_xpath = "//*[@{0}='{1}']//table//td".format(
                    day_table_identifier, end_calendar.get_attribute('id'))
            else:
                end_days_xpath = "//*[@{0}='{1}']//table//td".format(
                    day_table_identifier, day_table_class_name)
            all_days = self.driver.find_elements_by_xpath(end_days_xpath)

            for elem in all_days:
                if current_day_identifier == '':
                    if elem.text == str(end_date.day):
                        elem.click()
                else:
                    if (elem.text == str(end_date.day)
                            and elem.get_attribute('class')
                            == current_day_identifier):
                        elem.click()
        except NoSuchElementException:
            raise RuntimeError('Generierung des {0}-Kontoauszugs konnte nicht '
                'gestartet werden.'.format(self.name))
            return -1
        except TimeoutException:
            raise RuntimeError('Generierung des {0}-Kontoauszugs hat zu lange '
                'gedauert.'.format(self.name))
            return -1

        return 0

    def download_statement(self, download_btn, find_btn_by, actions=None):
        """
        Downloads the generated account statement and checks
        if the download was successful. If the download was successful,
        it will also call the rename_statement function to rename
        the downloaded file to the file name chosen by the user.

        Args:
            download_btn (str): id of the download button.
            find_btn_by (str): method for translating download_btn into
                web element.

        Keyword Args:
            actions (str): 'move to element' or None: some P2P sites
                require that the mouse hovers over a certain element
                in order to make the download button clickable.

        Returns:
            int: 0 on success, -1 on failure.
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
            return -1

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
                    return -1
                elif duration < 1:
                    time.sleep(1)
                    duration += 1

        if self.rename_statement() < 0:
            return -1

        return 0

    def wdwait(self, wait_until):
        """
        Shorthand for WebDriverWait.

        Args:
            wait_until (EC.*): expected condition for which the webdriver
                should wait.

        Returns:
            WebElement: WebElement which WebDriverWait waited for.
        """
        return WebDriverWait(self.driver, self.delay).until(wait_until)

    def clean_download_location(self):
        """
        Ensures that there are no old download files in download location.

        Makes sure that the download location does not contain
        old downloads. In case old downloads are detected they will be
        automatically removed. The user is informed via a warning message.

        Returns:
            int: 0 if download location is clean,
                -1 if user wants to manually delete the files.
        """
        file_list = glob.glob(
            'p2p_downloads/{0}.{1}'.format(
                self.default_file_name, self.file_format))
        if len(file_list) > 0:
            for file in file_list:
                try:
                    os.remove(file)
                except:
                    raise RuntimeError('Alte {0}-Downloads in ./p2p_downloads'
                        ' konnten nicht gelöscht werden. Bitte manuell '
                        'entfernen!'.format(self.name))
                    return -1

            raise RuntimeWarning('Alte {0}-Downloads in ./p2p_downloads wurden'
                'entfernt.'.format(self.name))

        return 0

    def rename_statement(self):
        """
        Will rename the downloaded statement from the
        default name chosen by the P2P platform to
        platform_name_statement.file_format.

        Returns:
            int: 0 on success, -1 on failure.
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
            return -1
        else:
            # This should never happen
            raise RuntimeError('Alte {0} Downloads in ./p2p_downloads '
                'entdeckt. Bitte zuerst entfernen.'.format(self.name))
            return -1

        return 0

def get_calendar_clicks(target_date,  start_date):
    """
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

def short_month_to_nbr(short_name):
    """
    Helper method for translating month short names to numbers

    Returns:
        str: two-digit month number padded with 0
    """
    short_month_to_nbr = {
        'Jan': '01',  'Feb': '02', 'Mrz': '03', 'Mar': '03',
        'Apr': '04', 'Mai': '05', 'May': '05', 'Jun': '06', 'Jul': '07',
        'Aug': '08', 'Sep': '09', 'Okt': '10', 'Oct': '10', 'Nov': '11',
        'Dez': '12', 'Dec': '12'
    }

    return short_month_to_nbr[short_name]

def nbr_to_short_month(nbr):
    """
    Helper method for translating numbers to month short names

    Returns:
        str: month short name
    """
    # Only German locale is used so far
    nbr_to_short_month = {
        '01': 'Jan', '02': 'Feb', '03': 'Mrz', '04': 'Apr', '05': 'Mai',
        '06': 'Jun', '07': 'Jul', '08': 'Aug', '09': 'Sep', '10': 'Okt',
        '11': 'Nov', '12': 'Dez'
    }

    return nbr_to_short_month[nbr]

def open_selenium_bondora(start_date, end_date):
    """
    Generates the Bondora account statement for given date range.

    Args:
        start_date (datetime.date): Start of date range for which account
            statement must be generated.
        end_date (datetime.date): End of date range for which account
            statement must be generated.

    Returns:
        int: 0 on success, -1 on failure
    """
    bondora = P2P(
        'Bondora', 'https://www.bondora.com/de/login',
        'https://www.bondora.com/de/cashflow',
        logout_url='https://www.bondora.com/de/authorize/logout')
    driver = bondora.driver

    if bondora.open_start_page(
            EC.element_to_be_clickable((By.NAME, 'Email'))) < 0:
        return -1

    if bondora.log_into_page(
            name_field='Email', password_field='Password',
            wait_until=EC.element_to_be_clickable(
                (By.LINK_TEXT, 'Cashflow'))) < 0:
        return -1

    if bondora.open_account_statement_page(
            title='Cashflow', element_to_check='StartYear') < 0:
        return -1

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

    search_button_xpath = ('//*[@id="page-content-wrapper"]/div/div/div[1]/'
                           'form/div[3]/button')
    start_date_xpath = ('/html/body/div[1]/div/div/div/div[3]/div/table/tbody/'
                        'tr[2]/td[1]/a')
    driver.find_element_by_xpath(search_button_xpath).click()
    bondora.wdwait(
        EC.text_to_be_present_in_element(
            (By.XPATH, start_date_xpath),
            '{0} {1}'.format(start_date.strftime('%b'), start_date.year)))

    cashflow_table = driver.find_element_by_id('cashflow-content')
    df = pd.read_html(
        cashflow_table.get_attribute("innerHTML"),  index_col=0,
        thousands='.', decimal=',')
    df[0].to_csv('p2p_downloads/bondora_statement.csv')

    bondora.logout_by_url(EC.title_contains('Einloggen'))

    driver.close()

    return 0

def open_selenium_mintos(start_date,  end_date):
    """
    Generates the Mintos account statement for given date range.

    Args:
        start_date (datetime.date): Start of date range for which
            account statement must be generated.
        end_date (datetime.date): End of date range for which
            account statement must be generated.

    Returns:
        int: 0 on success, -1 on failure.
    """
    today = datetime.today()
    default_file_name = '{0}{1}{2}-account-statement'.format(
        today.year,  today.strftime('%m'), today.strftime('%d'))
    mintos = P2P(
        'Mintos', 'https://www.mintos.com/de/',
        'https://www.mintos.com/de/kontoauszug/',
        default_file_name=default_file_name, file_format='xlsx')

    if mintos.clean_download_location() < 0:
        return -1

    if mintos.open_start_page(
            EC.element_to_be_clickable((By.NAME, 'MyAccountButton'))) < 0:
        return -1

    if mintos.log_into_page(
            name_field='_username', password_field='_password',
            wait_until=EC.element_to_be_clickable(
                (By.LINK_TEXT, 'Kontoauszug')),
            login_field='MyAccountButton',  find_login_by=By.NAME) < 0:
        return -1

    if mintos.open_account_statement_page(
            'Account Statement', 'period-from') < 0:
        return -1

    if mintos.generate_statement_direct(
            start_date, end_date, 'period-from', 'period-to', '%d.%m.%Y',
            wait_until=EC.presence_of_element_located(
                (By.ID, 'export-button')),
            submit_btn='filter-button', find_submit_btn_by=By.ID) < 0:
        return -1

    if mintos.download_statement('export-button', By.ID) < 0:
        success = -1
    else:
        success = 0

    mintos.logout_by_button(
        "//a[contains(@href,'logout')]",
        By.XPATH, EC.title_contains('Vielen Dank'))

    mintos.driver.close()

    return success

def open_selenium_robocash(start_date,  end_date):
    """
    Generates the Robocash account statement for given date range.

    Args:
        start_date (datetime.date): Start of date range for which account
            statement must be generated.
        end_date (datetime.date): End of date range for which account
            statement must be generated.

    Returns:
        int: 0 on success, -1 on failure
    """
    robocash = P2P(
        'Robocash', 'https://robo.cash/de',
        'https://robo.cash/de/cabinet/statement',
        logout_url='https://robo.cash/de/logout')

    if robocash.open_start_page(
            EC.presence_of_element_located(
                (By.XPATH, '/html/body/header/div/div/div[3]/a[1]')),
            'Robo.cash') < 0:
        return -1

    if robocash.log_into_page(
            name_field='email', password_field='password',
            wait_until=EC.element_to_be_clickable(
                (By.XPATH, '/html/body/header/div/div/div[2]/nav/ul/li[3]/a')),
            login_field='/html/body/header/div/div/div[3]/a[1]') < 0:
        return -1

    if robocash.open_account_statement_page(
            title='Kontoauszug', element_to_check='new_statement') < 0:
        return -1

    try:
        robocash.driver.find_element_by_id('new_statement').click()
    except NoSuchElementException:
        raise RuntimeError(
            'Generierung des Robocash-Kontoauszugs konnte nicht gestartet '
            'werden.')
        return -1

    if robocash.generate_statement_direct(
            start_date, end_date, 'date-after', 'date-before', '%Y-%m-%d') < 0:
        return -1

    # Robocash does not automatically show download button after statement
    # generation is done. An explicit reload of the page is needed.
    present = False
    wait = 0
    while not present:
        try:
            robocash.driver.get(robocash.statement_url)
            robocash.wdwait(
                EC.element_to_be_clickable((By.ID, 'download_statement')))
            present = True
        except TimeoutException:
            wait += 1
            if wait > 10:  # Roughly 10*delay=30 seconds
                raise RuntimeError(
                    'Generierung des Robocash-Kontoauszugs hat zu lange '
                    'gedauert!')
                return -1

    download_url = robocash.driver.find_element_by_id(
        'download_statement').get_attribute('href')
    driver_cookies = robocash.driver.get_cookies()
    cookies_copy = {}
    for driver_cookie in driver_cookies:
        cookies_copy[driver_cookie["name"]] = driver_cookie["value"]
    r = requests.get(download_url, cookies=cookies_copy)
    with open('p2p_downloads/robocash_statement.xls', 'wb') as output:
        output.write(r.content)

    robocash.logout_by_url(EC.title_contains('Willkommen'))

    robocash.driver.close()

    return 0

def open_selenium_swaper(start_date,  end_date):
    """
    Generates the Swaper account statement for given date range.

    Args:
        start_date (datetime.date): Start of date range for which account
            statement must be generated.
        end_date (datetime.date): End of date range for which account
            statement must be generated.

    Returns:
        int: 0 on success, -1 on failure
    """
    swaper = P2P(
        'Swaper', 'https://www.swaper.com/#/dashboard',
        'https://www.swaper.com/#/overview/account-statement',
        default_file_name='excel-storage*', file_format='xlsx')

    if swaper.clean_download_location() < 0:
        return -1

    if swaper.open_start_page(
            EC.presence_of_element_located((By.NAME, 'email'))) < 0:
        return -1

    if swaper.log_into_page(
            'email', 'password',
            EC.presence_of_element_located((By.ID, 'open-investments')),
            fill_delay=0.5) < 0:
        return -1

    if swaper.open_account_statement_page(
            title='Swaper', element_to_check='account-statement') < 0:
        return -1

    calendar_id_by = 'class'
    calendar_id = 'datepicker-container'
    arrows = ['icon icon icon-left', 'icon icon icon-right',  'div']
    days_table = ['', 'id', ' ',  True]
    default_dates = [datetime.today().replace(day=1),  datetime.now()]

    if swaper.generate_statement_calendar(
            start_date, end_date, default_dates, arrows, days_table,
            calendar_id_by,  calendar_id) < 0:
        return -1

    download_button_xpath = ('//*[@id="account-statement"]/div[3]/div[4]/div/'
                             'div[1]/a/div[1]/div/span[2]')
    if swaper.download_statement(download_button_xpath, By.XPATH) < 0:
        success = -1
    else:
        success = 0

    swaper.logout_by_button(
        '//*[@id="logout"]/span[1]/span', By.XPATH,
        EC.presence_of_element_located((By.ID, 'about')))

    swaper.driver.close()

    return success

def open_selenium_peerberry(start_date,  end_date):
    """
    Generates the PeerBerry account statement for given date range.

    Args:
        start_date (datetime.date): Start of date range for which account
            statement must be generated.
        end_date (datetime.date): End of date range for which account
            statement must be generated.

    Returns:
        int: 0 on success, -1 on failure
    """
    peerberry = P2P(
        'PeerBerry', 'https://peerberry.com/de/login',
        'https://peerberry.com/de/statement',
        default_file_name='transactions', file_format='csv')

    if peerberry.clean_download_location() < 0:
        return -1

    if peerberry.open_start_page(
            EC.element_to_be_clickable((By.NAME, 'email')),
            'PeerBerry.com') < 0:
        return -1

    if peerberry.log_into_page(
            'email', 'password',
            EC.element_to_be_clickable((By.LINK_TEXT, 'Kontoauszug'))) < 0:
        return -1

    if peerberry.open_account_statement_page(
            'Kontoauszug', 'startDate', check_by=By.NAME) < 0:
        return -1

    # Close the cookie policy, if present
    try:
        peerberry.driver.find_element_by_xpath(
            '//*[@id="app"]/div/div/div/div[4]/div/div/div[1]').click()
    except NoSuchElementException:
        pass

    # Create account statement for given date range
    default_dates = [datetime.now(),  datetime.now()]
    arrows = ['rdtPrev', 'rdtNext', 'th']
    calendar_id_by = 'name'
    calendar_id = ['startDate',  'endDate']
    days_table = ['rdtDays', 'class', 'rdtDay', False]

    if peerberry.generate_statement_calendar(
            start_date, end_date,  default_dates, arrows, days_table,
            calendar_id_by, calendar_id) < 0:
        return -1

    # Generate account statement
    start_balance_xpath = (
        '/html/body/div[1]/div/div/div/div[2]/div/div[2]/div[2]/div/div/'
        'div[1]')
    statement_button_xpath = (
        '/html/body/div[1]/div/div/div/div[2]/div/div[2]/div[1]/div/div[2]/'
        'div/div[2]/div/span')
    try:
        peerberry.driver.find_element_by_xpath(statement_button_xpath).click()
        peerberry.wdwait(
            EC.text_to_be_present_in_element(
                ((By.XPATH, start_balance_xpath)),
                'Eröffnungssaldo '+str(start_date).format('%Y-%m-%d')))
    except NoSuchElementException:
        raise RuntimeError('Generierung des {0}-Kontoauszugs konnte nicht '
            'gestartet werden.'.format(peerberry.name))
        return -1
    except TimeoutException:
        raise RuntimeError('Generierung des {0}-Kontoauszugs hat zu lange '
            'gedauert.'.format(peerberry.name))
        return -1

    if peerberry.download_statement(
            '//*[@id="app"]/div/div/div/div[2]/div/div[2]/div[3]/div[2]/div',
            By.XPATH, actions='move_to_element') < 0:
        success = -1
    else:
        success = 0

    logout_button_xpath = ('//*[@id="app"]/div/div/div/div[1]/div[1]/div/div/'
                           'div[2]/div')
    peerberry.logout_by_button(
        logout_button_xpath, By.XPATH, EC.title_contains('Einloggen'))

    peerberry.driver.close()

    return success

def open_selenium_estateguru(start_date,  end_date):
    """
    Generates the Estateguru account statement for given date range.

    Args:
        start_date (datetime.date): Start of date range for which account
            statement must be generated.
        end_date (datetime.date): End of date range for which account
            statement must be generated.

    Returns:
        int: 0 on success, -1 on failure
    """
    today = datetime.today()
    default_file_name = 'payments_{0}-{1}-{2}*'.format(today.year, 
        today.strftime('%m'), today.strftime('%d'))
    estateguru = P2P(
        'Estateguru', 'https://estateguru.co/portal/login/auth?lang=de',
        'https://estateguru.co/portal/portfolio/account',
        default_file_name=default_file_name, file_format='csv',
        logout_url='https://estateguru.co/portal/logout/index')

    if estateguru.open_start_page(
            EC.element_to_be_clickable((By.NAME, 'username')),
            'Sign in/Register') < 0:
        return -1

    if estateguru.log_into_page(
            'username', 'password',
            EC.element_to_be_clickable((By.LINK_TEXT, 'KONTOSTAND'))) < 0:
        return -1

    check_xpath = ('/html/body/section/div/div/div/div[2]/section[1]/div/div/'
                   'div[2]/div/form/div[2]/ul/li[5]/a')
    if estateguru.open_account_statement_page(
            'Übersicht', element_to_check=check_xpath, check_by=By.XPATH) < 0:
        return -1

    #Estateguru does not provide functionality for filtering payment
    #dates. Therefore we download the statement which includes all cashflows
    #ever generated for this account.
    select_btn_xpath = ('/html/body/section/div/div/div/div[2]/section[2]/'
                        'div[1]/div[2]/button')
    estateguru.driver.find_element_by_xpath(select_btn_xpath).click()
    estateguru.wdwait(EC.element_to_be_clickable((By.LINK_TEXT, 'CSV')))
    estateguru.download_statement('CSV', By.LINK_TEXT)

    estateguru.logout_by_url(EC.title_contains('Einloggen/Registrieren'))

    estateguru.driver.close()

    return 0

def open_selenium_iuvo(start_date,  end_date):
    """
    Generates the Iuvo account statement for given date range.

    Args:
        start_date (datetime.date): Start of date range for which account
            statement must be generated.
        end_date (datetime.date): End of date range for which account
            statement must be generated.

    Returns:
        int: 0 on success, -1 on failure
    """
    iuvo = P2P(
        'Iuvo',
        'https://www.iuvo-group.com/de/login/',
        'https://www.iuvo-group.com/de/account-statement/')
    driver = iuvo.driver

    if iuvo.open_start_page(
            EC.element_to_be_clickable((By.NAME, 'login'))) < 0:
        return -1

    if iuvo.log_into_page(
            'login', 'password',
            EC.element_to_be_clickable(
                (By.ID, 'p2p_btn_deposit_page_add_funds'))) < 0:
        return -1

    # Click away cookie policy, if present
    try:
        driver.find_element_by_id(
            'CybotCookiebotDialogBodyButtonAccept').click()
    except NoSuchElementException:
        pass

    if iuvo.open_account_statement_page('Kontoauszug', 'date_from') < 0:
        return -1

    # Since Dec 2018 Iuvo only provides aggregated cashflows
    # for the whole requested date range, no more detailed information
    # Workaround to get monthly data: create account statement for
    # each month in date range

    # Get all required monthly date ranges
    months = []
    m = start_date
    while m < end_date:
        start_of_month = date(m.year, m.month, 1)
        end_of_month = date(m.year, m.month, calendar.monthrange(
            m.year, m.month)[1])
        months.append([start_of_month, end_of_month])
        m = m + timedelta(days=31)

    df_result = None
    # First entry: name of start balance -> "Anfangsbestand"
    # Second entry: actual start balance
    start_balance_xpath = [
        ('/html/body/div[5]/main/div/div/div/div[4]/div/table/thead/tr[1]/'
         'td[1]/strong'),
        ('/html/body/div[5]/main/div/div/div/div[4]/div/table/thead/tr[1]/'
         'td[2]/strong')
    ]
    for month in months:
        start_balance = driver.find_element_by_xpath(
            start_balance_xpath[1]).text

        if iuvo.generate_statement_direct(
                month[0], month[1], 'date_from', 'date_to', '%Y-%m-%d',
                wait_until=EC.text_to_be_present_in_element(
                    (By.XPATH, start_balance_xpath[0]),
                    'Anfangsbestand'),
                submit_btn='account_statement_filters_btn',
                find_submit_btn_by=By.ID) < 0:
            return -1

        # Read statement from page
        new_start_balance = driver.find_element_by_xpath(
            start_balance_xpath[1]).text
        if new_start_balance == start_balance:
            # If the start balance didn't change, the calculation is most
            # likely not finished yet
            # TODO: find better way to wait until new statement is generated
            time.sleep(3)
        statement_table = driver.find_element_by_class_name('table-responsive')
        df = pd.read_html(
            statement_table.get_attribute("innerHTML"), index_col=0)[0]
        df = df.T
        df['Datum'] = month[0].strftime('%d.%m.%Y')

        if df_result is None:
            df_result = df
        else:
            df_result = df_result.append(df, sort=True)

    df_result.to_csv('p2p_downloads/iuvo_statement.csv')

    iuvo.logout_by_button(
        'p2p_logout', By.ID, EC.title_contains('Investieren Sie in Kredite'),
        hover_elem='User name', hover_elem_by=By.LINK_TEXT)

    driver.close()

    return 0

def open_selenium_grupeer(start_date,  end_date):
    """
    Generates the Grupeer account statement for given date range.

    Args:
        start_date (datetime.date): Start of date range for which account
            statement must be generated.
        end_date (datetime.date): End of date range for which account
            statement must be generated.

    Returns:
        int: 0 on success, -1 on failure
    """
    grupeer = P2P(
        'Grupeer',
        'https://www.grupeer.com/de/login',
        'https://www.grupeer.com/de/account-statement',
        default_file_name='Account statement',
        file_format='xlsx')

    if grupeer.clean_download_location() < 0:
        return -1

    if grupeer.open_start_page(
            EC.element_to_be_clickable((By.NAME, 'email'))) < 0:
        return -1

    if grupeer.log_into_page(
            'email', 'password',
            EC.element_to_be_clickable(
                (By.LINK_TEXT, 'Meine Investments'))) < 0:
        return -1

    if grupeer.open_account_statement_page('Account Statement', 'from') < 0:
        return -1

    if grupeer.generate_statement_direct(
            start_date, end_date, 'from', 'to', '%d.%m.%Y',
            wait_until=EC.text_to_be_present_in_element(
                (By.CLASS_NAME, 'balance-block'),
                'Bilanz geöffnet am '+str(start_date.strftime('%d.%m.%Y'))),
            submit_btn='submit', find_submit_btn_by=By.NAME) < 0:
        return -1

    if grupeer.download_statement('excel', By.NAME) < 0:
        success = -1
    else:
        success = 0

    grupeer.logout_by_button(
        'Ausloggen',
        By.LINK_TEXT, EC.title_contains('P2P Investitionsplattform Grupeer'),
        '/html/body/div[4]/header/div/div/div[2]/div[1]/div/div/ul/li/a/span',
        By.XPATH)

    grupeer.driver.close()

    return success

def open_selenium_dofinance(start_date,  end_date):
    """
    Generates the Dofinance account statement for given date range.

    Args:
        start_date (datetime.date): Start of date range for which account
            statement must be generated.
        end_date (datetime.date): End of date range for which account
            statement must be generated.

    Returns:
        int: 0 on success, -1 on failure
    """
    default_file_name = 'Statement_{0} 00_00_00-{1} 23_59_59'.format(
        start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
    dofinance = P2P(
        'DoFinance', 'https://www.dofinance.eu/de/users/login',
        'https://www.dofinance.eu/de/users/statement',
        logout_url='https://www.dofinance.eu/de/users/logout',
        default_file_name=default_file_name,  file_format='xlsx')

    if dofinance.clean_download_location() < 0:
        return -1

    if dofinance.open_start_page(
            EC.element_to_be_clickable((By.NAME, 'email')),
            title_check='Anmeldung') < 0:
        return -1

    if dofinance.log_into_page(
            'email', 'password',
            EC.element_to_be_clickable((By.LINK_TEXT, 'TRANSAKTIONEN'))) < 0:
        return -1

    if dofinance.open_account_statement_page('Transaktionen', 'date-from') < 0:
        return -1

    if dofinance.generate_statement_direct(
            start_date, end_date, 'date-from', 'date-to', '%d.%m.%Y',
            wait_until=EC.element_to_be_clickable((By.NAME, 'xls'))) < 0:
        return -1

    if dofinance.download_statement('xls', By.NAME) < 0:
        success = -1
    else:
        success = 0

    dofinance.logout_by_url(EC.title_contains('Kreditvergabe Plattform'))

    dofinance.driver.close()

    return success

def open_selenium_twino(start_date,  end_date):
    """
    Generates the Twino account statement for given date range.

    Args:
        start_date (datetime.date): Start of date range for which account
            statement must be generated.
        end_date (datetime.date): End of date range for which account
            statement must be generated.

    Returns:
        int: 0 on success, -1 on failure
    """
    statement_url = ('https://www.twino.eu/de/profile/investor/my-investments/'
                     'account-transactions')
    twino = P2P(
        'Twino', 'https://www.twino.eu/de/',
        statement_url,
        default_file_name='account_statement_*',
        file_format='xlsx')

    if twino.clean_download_location() < 0:
        return -1

    login_btn_xpath = ('/html/body/div[1]/div[2]/div[1]/header[1]/div/nav/div/'
                       'div[1]/button')
    start_date_xpath = '//*[@date-picker="filterData.processingDateFrom"]'
    end_date_xpath = '//*[@date-picker="filterData.processingDateTo"]'

    if twino.open_start_page(
            EC.element_to_be_clickable((By.XPATH, login_btn_xpath)),
            title_check='TWINO') < 0:
        return -1

    statement_xpath = ('//a[@href="/de/profile/investor/my-investments/'
                       'individual-investments"]')
    if twino.log_into_page(
            'email', 'login-password',
            EC.element_to_be_clickable((By.XPATH, statement_xpath)),
            login_field=login_btn_xpath, find_login_by=By.XPATH) < 0:
        return -1

    if twino.open_account_statement_page(
            'TWINO', start_date_xpath, check_by=By.XPATH) < 0:
        return -1

    if twino.generate_statement_direct(
            start_date, end_date, start_date_xpath, end_date_xpath,
            '%d.%m.%Y', find_elem_by=By.XPATH,
            wait_until=EC.element_to_be_clickable(
                (By.CSS_SELECTOR, '.accStatement__pdf'))) < 0:
        return -1

    if twino.download_statement('.accStatement__pdf', By.CSS_SELECTOR) < 0:
        success = -1
    else:
        success = 0

    twino.logout_by_button(
        '//a[@href="/logout"]',
        By.XPATH, EC.element_to_be_clickable((By.XPATH, login_btn_xpath)))

    twino.driver.close()

    return success
