# -*- coding: utf-8 -*-
# Copyright 2018-19 Niko Sandschneider

"""
p2p_platforms contains the main code for handling the P2P platforms.

Each platform is created as an instance of the P2P class.

.. moduleauthor:: Niko Sandschneider <nsandschn@gmx.de>

"""

from datetime import datetime
import time
from typing import Tuple, Union

import pandas as pd
import requests
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException

from P2P import P2P
import p2p_helper

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
                'Cashflow', (By.ID, 'StartYear')):
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

        if (p2p_helper.short_month_to_nbr(start_month)
                != start_date.strftime('%m')):
            select = Select(driver.find_element_by_id('StartMonth'))
            select.select_by_visible_text(p2p_helper.nbr_to_short_month(
                start_date.strftime('%m')))

        if end_year != end_date.year:
            select = Select(driver.find_element_by_id('EndYear'))
            select.select_by_visible_text(str(end_date.year))

        if p2p_helper.short_month_to_nbr(end_month) != end_date.strftime('%m'):
            select = Select(driver.find_element_by_id('EndMonth'))
            select.select_by_visible_text(p2p_helper.nbr_to_short_month(
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
        'login': 'https://www.mintos.com/de/login',
        'statement': 'https://www.mintos.com/de/kontoauszug/'}
    xpaths = {
        'logout_btn': "//a[contains(@href,'logout')]"}
    today = datetime.today()
    default_file_name = '{0}{1}{2}-account-statement.xlsx'.format(
        today.year, today.strftime('%m'), today.strftime('%d'))

    with P2P(
            'Mintos', urls, EC.title_contains('Vielen Dank'),
            logout_locator=(By.XPATH, xpaths['logout_btn']),
            default_file_name=default_file_name) as mintos:

        if not mintos.clean_download_location():
            return False

        if not mintos.open_start_page(
                EC.element_to_be_clickable((By.NAME, '_username'))):
            return False

        if not mintos.log_into_page(
                '_username', '_password', credentials,
                EC.element_to_be_clickable((By.LINK_TEXT, 'Kontoauszug'))):
            return False

        if not mintos.open_account_statement_page(
                'Account Statement', (By.ID, 'period-from')):
            return False

        if not mintos.generate_statement_direct(
                start_date, end_date, (By.ID, 'period-from'),
                (By.ID, 'period-to'), '%d.%m.%Y',
                wait_until=EC.presence_of_element_located(
                    (By.ID, 'export-button')),
                submit_btn_locator=(By.ID, 'filter-button')):
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
    xpaths = {'login_field': '/html/body/header/div/div[2]/a'}

    with P2P('Robocash', urls, EC.title_contains('Willkommen')) as robocash:

        if not robocash.open_start_page(
                EC.element_to_be_clickable(
                    (By.XPATH, xpaths['login_field']))):
            return False

        if not robocash.log_into_page(
                'email', 'password', credentials,
                EC.element_to_be_clickable((By.LINK_TEXT, 'Kontoauszug')),
                login_locator=(By.XPATH, xpaths['login_field'])):
            return False

        if not robocash.open_account_statement_page(
                'Kontoauszug', (By.ID, 'new_statement')):
            return False

        try:
            robocash.driver.find_element_by_id('new_statement').click()
        except NoSuchElementException:
            raise RuntimeError(
                'Generierung des Robocash-Kontoauszugs konnte nicht gestartet '
                'werden.')

        if not robocash.generate_statement_direct(
                start_date, end_date, (By.ID, 'date-after'),
                (By.ID, 'date-before'), '%Y-%m-%d'):
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
        data = requests.get(download_url, cookies=cookies_copy)
        with open('p2p_downloads/robocash_statement.xlsx', 'wb') as output:
            output.write(data.content)

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
            'Swaper', urls, EC.presence_of_element_located((By.ID, 'about')),
            logout_locator=(By.XPATH, xpaths['logout_btn']),
            default_file_name='excel-storage*.xlsx') as swaper:

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
                'Swaper', (By.ID, 'account-statement')):
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
        default_dates = (datetime.today().replace(day=1), datetime.now())

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
            'PeerBerry', urls, EC.title_contains('Einloggen'),
            logout_locator=(By.XPATH, xpaths['logout_btn']),
            default_file_name='transactions.csv') as peerberry:

        if not peerberry.clean_download_location():
            return False

        if not peerberry.open_start_page(
                EC.element_to_be_clickable((By.NAME, 'email'))):
            return False

        if not peerberry.log_into_page(
                'email', 'password', credentials,
                EC.element_to_be_clickable((By.LINK_TEXT, 'Kontoauszug'))):
            return False

        if not peerberry.open_account_statement_page(
                'Kontoauszug', (By.NAME, 'startDate')):
            return False

        # Close the cookie policy, if present
        try:
            peerberry.driver.find_element_by_xpath(
                xpaths['cookie_policy']).click()
        except NoSuchElementException:
            pass

        # Create account statement for given date range
        default_dates = (datetime.now(), datetime.now())
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
    default_file_name = 'payments_{0}-{1}-{2}*.csv'.format(
        today.year, today.strftime('%m'), today.strftime('%d'))
    with P2P(
            'Estateguru', urls,
            EC.element_to_be_clickable((By.NAME, 'username')),
            default_file_name=default_file_name) as estateguru:

        if not estateguru.open_start_page(
                EC.element_to_be_clickable((By.NAME, 'username'))):
            return False

        if not estateguru.log_into_page(
                'username', 'password', credentials,
                EC.element_to_be_clickable((By.LINK_TEXT, 'KONTOSTAND'))):
            return False

        if not estateguru.open_account_statement_page(
                'Übersicht', (By.XPATH, xpaths['account_statement_check'])):
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
            'Iuvo', urls, EC.title_contains('Investieren Sie in Kredite'),
            logout_locator=(By.ID, 'p2p_logout'),
            hover_locator=(By.LINK_TEXT, 'User name')) as iuvo:

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

        if not iuvo.open_account_statement_page(
                'Kontoauszug', (By.ID, 'date_from')):
            return False

        # Since Dec 2018 Iuvo only provides aggregated cashflows
        # for the whole requested date range, no more detailed information
        # Workaround to get monthly data: create account statement for
        # each month in date range

        # Get all required monthly date ranges
        months = p2p_helper.get_list_of_months(start_date, end_date)

        df_result = None

        for month in months:
            start_balance = driver.find_element_by_xpath(
                xpaths['start_balance_value']).text

            if not iuvo.generate_statement_direct(
                    month[0], month[1], (By.ID, 'date_from'),
                    (By.ID, 'date_to'), '%Y-%m-%d',
                    wait_until=EC.text_to_be_present_in_element(
                        (By.XPATH, xpaths['start_balance_name']),
                        'Anfangsbestand'),
                    submit_btn_locator=(
                        By.ID, 'account_statement_filters_btn')):
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
        'logout_hover': ('/html/body/div[4]/header/div/div/div[2]/div[1]/'
                         'div/div/ul/li/a/span')}

    with P2P(
            'Grupeer', urls,
            EC.title_contains('P2P Investitionsplattform Grupeer'),
            (By.LINK_TEXT, 'Ausloggen'),
            default_file_name='Account statement.xlsx',
            hover_locator=(By.XPATH, xpaths['logout_hover'])) as grupeer:

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
                'Account Statement', (By.ID, 'from')):
            return False

        if not grupeer.generate_statement_direct(
                start_date, end_date, (By.ID, 'from'), (By.ID, 'to'),
                '%d.%m.%Y', wait_until=EC.text_to_be_present_in_element(
                    (By.CLASS_NAME, 'balance-block'),
                    'Bilanz geöffnet am '
                    + str(start_date.strftime('%d.%m.%Y'))),
                submit_btn_locator=(By.NAME, 'submit')):
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
    default_file_name = 'Statement_{0} 00_00_00-{1} 23_59_59.xlsx'.format(
        start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
    with P2P(
            'DoFinance', urls, EC.title_contains('Kreditvergabe Plattform'),
            default_file_name=default_file_name) as dofinance:

        if not dofinance.clean_download_location():
            return False

        if not dofinance.open_start_page(
                EC.element_to_be_clickable((By.NAME, 'email'))):
            return False

        if not dofinance.log_into_page(
                'email', 'password', credentials,
                EC.element_to_be_clickable((By.LINK_TEXT, 'TRANSAKTIONEN'))):
            return False

        if not dofinance.open_account_statement_page(
                'Transaktionen', (By.ID, 'date-from')):
            return False

        if not dofinance.generate_statement_direct(
                start_date, end_date, (By.ID, 'date-from'), (By.ID, 'date-to'),
                '%d.%m.%Y',
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
            'Twino', urls,
            EC.element_to_be_clickable((By.XPATH, xpaths['login_btn'])),
            logout_locator=(By.XPATH, xpaths['logout_btn']),
            default_file_name='account_statement_*.xlsx') as twino:

        if not twino.clean_download_location():
            return False

        if not twino.open_start_page(
                EC.element_to_be_clickable((By.XPATH, xpaths['login_btn']))):
            return False

        if not twino.log_into_page(
                'email', 'login-password', credentials,
                EC.element_to_be_clickable((By.XPATH, xpaths['statement'])),
                login_locator=(By.XPATH, xpaths['login_btn'])):
            return False

        if not twino.open_account_statement_page(
                'TWINO', (By.XPATH, xpaths['start_date'])):
            return False

        if not twino.generate_statement_direct(
                start_date, end_date, (By.XPATH, xpaths['start_date']),
                (By.XPATH, xpaths['end_date']), '%d.%m.%Y',
                wait_until=EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, '.accStatement__pdf'))):
            return False

        success = twino.download_statement(
            '.accStatement__pdf', By.CSS_SELECTOR)

    return success
