# -*- coding: utf-8 -*-
# Copyright 2018-19 Niko Sandschneider

"""
p2p_platforms contains the main code for handling the P2P platforms.

Each platform is created as an instance of the P2P class.

.. moduleauthor:: Niko Sandschneider <nsandschn@gmx.de>

"""

from datetime import datetime
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
        date_range: Tuple[datetime.date, datetime.date],
        credentials: Tuple[str, str]) -> None:
    """
    Generate and download the Bondora account statement for given date range.

    Args:
        date_range (tuple(datetime.date, datetime.date)): date range
            (start_date, end_date) for which the account statements must
            be generated.
        credentials (tuple[str, str]): (username, password) for Bondora

    """
    # TODO: check if the input variables are sane, also for the other
    # open_selenium_* functions
    urls = {
        'login': 'https://www.bondora.com/de/login',
        'logout': 'https://www.bondora.com/de/authorize/logout',
        'statement': 'https://www.bondora.com/de/cashflow'}
    xpaths = {
        'no_payments': '/html/body/div[1]/div/div/div/div[3]/div',
        'search_btn': ('//*[@id="page-content-wrapper"]/div/div/div[1]/form/'
                       'div[3]/button'),
        'start_date': ('/html/body/div[1]/div/div/div/div[3]/div/table/tbody/'
                       'tr[2]/td[1]/a')}

    with P2P('Bondora', urls, EC.title_contains('Einloggen')) as bondora:

        driver = bondora.driver

        bondora.open_start_page(
            EC.element_to_be_clickable((By.NAME, 'Email')))

        bondora.log_into_page(
            'Email', 'Password', credentials,
            EC.element_to_be_clickable((By.LINK_TEXT, 'Cashflow')))

        bondora.open_account_statement_page('Cashflow', (By.ID, 'StartYear'))

        # Get the default values for start and end date
        start_year = Select(
            driver.find_element_by_id('StartYear')).first_selected_option.text
        start_month = Select(
            driver.find_element_by_id('StartMonth')).first_selected_option.text
        end_year = Select(
            driver.find_element_by_id('EndYear')).first_selected_option.text
        end_month = Select(
            driver.find_element_by_id('EndMonth')).first_selected_option.text

        # Change the date values to the given start and end dates
        if start_year != date_range[0].year:
            select = Select(driver.find_element_by_id('StartYear'))
            select.select_by_visible_text(str(date_range[0].year))

        if (p2p_helper.short_month_to_nbr(start_month)
                != date_range[0].strftime('%m')):
            select = Select(driver.find_element_by_id('StartMonth'))
            select.select_by_visible_text(p2p_helper.nbr_to_short_month(
                date_range[0].strftime('%m')))

        if end_year != date_range[1].year:
            select = Select(driver.find_element_by_id('EndYear'))
            select.select_by_visible_text(str(date_range[1].year))

        if p2p_helper.short_month_to_nbr(end_month) \
                != date_range[1].strftime('%m'):
            select = Select(driver.find_element_by_id('EndMonth'))
            select.select_by_visible_text(p2p_helper.nbr_to_short_month(
                date_range[1].strftime('%m')))

        # Start the account statement generation
        driver.find_element_by_xpath(xpaths['search_btn']).click()

        # Wait until statement generation is finished. If the statement cannot
        # be found a TimeoutException is raised. That can happen in case of
        # errors or when there were no cashflows in the requested period.
        try:
            bondora.wdwait(
                EC.text_to_be_present_in_element(
                    (By.XPATH, xpaths['start_date']),
                    '{0} {1}'.format(
                        date_range[0].strftime('%b'), date_range[0].year)))
        except TimeoutException as err:
            if 'Keine Zahlungen gefunden' in \
                    driver.find_element_by_xpath(xpaths['no_payments']).text:
                raise RuntimeError(
                    'Bondora: keine Zahlungen im angeforderten Zeitraum '
                    'vorhanden!')
            else:
                raise TimeoutException(err)

        # Scrape the cashflows from the web site and write them to a csv file
        cashflow_table = driver.find_element_by_id('cashflow-content')
        df = pd.read_html(
            cashflow_table.get_attribute("innerHTML"), index_col=0,
            thousands='.', decimal=',')[0]
        df.to_csv('p2p_downloads/bondora_statement.csv')

def open_selenium_mintos(
        date_range: Tuple[datetime.date, datetime.date],
        credentials: Tuple[str, str]) -> None:
    """
    Generate and download the Mintos account statement for given date range.

    Args:
        date_range (tuple(datetime.date, datetime.date)): date range
            (start_date, end_date) for which the account statements must
            be generated.
        credentials (tuple[str, str]): (username, password) for Mintos

    """
    urls = {
        'login': 'https://www.mintos.com/de/login',
        'statement': 'https://www.mintos.com/de/kontoauszug/'}
    xpaths = {
        'logout_btn': "//a[contains(@href,'logout')]"}
    default_file_name = '{0}-account-statement.xlsx'.format(
        datetime.today().strftime('%Y%m%d'))

    with P2P(
            'Mintos', urls, EC.title_contains('Vielen Dank'),
            logout_locator=(By.XPATH, xpaths['logout_btn'])) as mintos:

        mintos.open_start_page(
            EC.element_to_be_clickable((By.NAME, '_username')))

        mintos.log_into_page(
            '_username', '_password', credentials,
            EC.element_to_be_clickable((By.LINK_TEXT, 'Kontoauszug')))

        mintos.open_account_statement_page(
            'Account Statement', (By.ID, 'period-from'))

        mintos.generate_statement_direct(
            date_range, (By.ID, 'period-from'),
            (By.ID, 'period-to'), '%d.%m.%Y',
            wait_until=EC.presence_of_element_located((By.ID, 'export-button')),
            submit_btn_locator=(By.ID, 'filter-button'))

        mintos.download_statement(default_file_name, 'export-button', By.ID)

def open_selenium_robocash(
        date_range: Tuple[datetime.date, datetime.date],
        credentials: Tuple[str, str]) -> None:
    """
    Generate and download the Robocash account statement for given date range.

    Args:
        date_range (tuple(datetime.date, datetime.date)): date range
            (start_date, end_date) for which the account statements must
            be generated.
        credentials (tuple[str, str]): (username, password) for Robocash

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

        robocash.open_start_page(
            EC.element_to_be_clickable((By.XPATH, xpaths['login_field'])))

        robocash.log_into_page(
            'email', 'password', credentials,
            EC.element_to_be_clickable((By.LINK_TEXT, 'Kontoauszug')),
            login_locator=(By.XPATH, xpaths['login_field']))

        robocash.open_account_statement_page(
            'Kontoauszug', (By.ID, 'new_statement'))

        try:
            robocash.driver.find_element_by_id('new_statement').click()
        except NoSuchElementException:
            raise RuntimeError(
                'Generierung des Robocash-Kontoauszugs konnte nicht gestartet '
                'werden.')

        robocash.generate_statement_direct(
            date_range, (By.ID, 'date-after'),
            (By.ID, 'date-before'), '%Y-%m-%d')

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
                if wait > 10:  # Roughly 10*delay seconds
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

def open_selenium_swaper(
        date_range: Tuple[datetime.date, datetime.date],
        credentials: Tuple[str, str]) -> None:
    """
    Generate and download the Swaper account statement for given date range.

    Args:
        date_range (tuple(datetime.date, datetime.date)): date range
            (start_date, end_date) for which the account statements must
            be generated.
        credentials (tuple[str, str]): (username, password) for Swaper

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
            logout_locator=(By.XPATH, xpaths['logout_btn'])) as swaper:

        swaper.open_start_page(
            EC.presence_of_element_located((By.NAME, 'email')))

        swaper.log_into_page(
            'email', 'password', credentials,
            EC.presence_of_element_located((By.ID, 'open-investments')),
            fill_delay=0.5)

        swaper.open_account_statement_page(
            'Swaper', (By.ID, 'account-statement'))

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

        swaper.generate_statement_calendar(
            date_range, default_dates, arrows, days_table,
            calendar_id_by, calendar_id)

        swaper.download_statement(
            'excel-storage*.xlsx', xpaths['download_btn'], By.XPATH)

def open_selenium_peerberry(
        date_range: Tuple[datetime.date, datetime.date],
        credentials: Tuple[str, str]) -> None:
    """
    Generate and download the PeerBerry account statement for given date range.

    Args:
        date_range (tuple(datetime.date, datetime.date)): date range
            (start_date, end_date) for which the account statements must
            be generated.
        credentials (tuple[str, str]): (username, password) for PeerBerry

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
            logout_locator=(By.XPATH, xpaths['logout_btn'])) as peerberry:

        peerberry.open_start_page(
            EC.element_to_be_clickable((By.NAME, 'email')))

        peerberry.log_into_page(
            'email', 'password', credentials,
            EC.element_to_be_clickable((By.LINK_TEXT, 'Kontoauszug')))

        peerberry.open_account_statement_page(
            'Kontoauszug', (By.NAME, 'startDate'))

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

        peerberry.generate_statement_calendar(
            date_range, default_dates, arrows, days_table,
            calendar_id_by, calendar_id)

        # After setting the dates, the statement button needs to be clicked in
        # order to actually generate the statement
        try:
            peerberry.driver.find_element_by_xpath(
                xpaths['statement_btn']).click()
            peerberry.wdwait(
                EC.text_to_be_present_in_element(
                    ((By.XPATH, xpaths['start_balance'])),
                    'Eröffnungssaldo '+str(date_range[0]).format('%Y-%m-%d')))
        except NoSuchElementException:
            raise RuntimeError('Generierung des PeerBerry-Kontoauszugs konnte '
                               'nicht gestartet werden.')
        except TimeoutException:
            raise RuntimeError('Generierung des PeerBerry-Kontoauszugs hat zu '
                               'lange gedauert.')

        peerberry.download_statement(
            'transactions.csv', xpaths['download_btn'], By.XPATH,
            actions='move_to_element')

def open_selenium_estateguru(
        date_range: Tuple[datetime.date, datetime.date],
        credentials: Tuple[str, str]) -> None:
    """
    Generate and download Estateguru account statement for given date range.

    Args:
        date_range (tuple(datetime.date, datetime.date)): date range
            (start_date, end_date) for which the account statements must
            be generated.
        credentials (tuple[str, str]): (username, password) for Estateguru

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
    default_file_name = 'payments_{0}*.csv'.format(
        datetime.today().strftime('%Y-%m-%d'))

    with P2P(
            'Estateguru', urls,
            EC.element_to_be_clickable((By.NAME, 'username'))) as estateguru:

        estateguru.open_start_page(
            EC.element_to_be_clickable((By.NAME, 'username')))

        estateguru.log_into_page(
            'username', 'password', credentials,
            EC.element_to_be_clickable((By.LINK_TEXT, 'KONTOSTAND')))

        estateguru.open_account_statement_page(
            'Übersicht', (By.XPATH, xpaths['account_statement_check']))

        # Estateguru does not provide functionality for filtering payment
        # dates. Therefore we download the statement which includes all
        # cashflows ever generated for this account. That also means that
        # date_range is not used for Estateguru. We keep it as input variable
        # anyway to be consistent with the other open_selenium_* functions.
        estateguru.driver.find_element_by_xpath(xpaths['select_btn']).click()
        estateguru.wdwait(EC.element_to_be_clickable((By.LINK_TEXT, 'CSV')))
        estateguru.download_statement(default_file_name, 'CSV', By.LINK_TEXT)

def open_selenium_iuvo(
        date_range: Tuple[datetime.date, datetime.date],
        credentials: Tuple[str, str]) -> None:
    """
    Generate and download the Iuvo account statement for given date range.

    Args:
        date_range (tuple(datetime.date, datetime.date)): date range
            (start_date, end_date) for which the account statements must
            be generated.
        credentials (tuple[str, str]): (username, password) for Iuvo.

    """
    urls = {
        'login': 'https://www.iuvo-group.com/de/login/',
        'statement': 'https://www.iuvo-group.com/de/account-statement/'}
    xpaths = {
        'statement_check': ('//*[@id="p2p_cont"]/div/div[6]/div/div/div/'
                            'strong[3]')}

    with P2P(
            'Iuvo', urls, EC.element_to_be_clickable((By.ID, 'einloggen')),
            logout_locator=(By.ID, 'p2p_logout'),
            hover_locator=(By.LINK_TEXT, 'User name')) as iuvo:

        driver = iuvo.driver

        iuvo.open_start_page(
            EC.element_to_be_clickable((By.NAME, 'login')))

        iuvo.log_into_page(
            'login', 'password', credentials,
            EC.element_to_be_clickable(
                (By.ID, 'p2p_btn_deposit_page_add_funds')))

        # Click away cookie policy, if present
        try:
            driver.find_element_by_id(
                'CybotCookiebotDialogBodyButtonAccept').click()
        except NoSuchElementException:
            pass

        iuvo.open_account_statement_page(
            'Kontoauszug', (By.ID, 'date_from'))

        # Since Dec 2018 Iuvo only provides aggregated cashflows
        # for the whole requested date range, no more detailed information
        # Workaround to get monthly data: create account statement for
        # each month in date range

        # Get all required monthly date ranges
        months = p2p_helper.get_list_of_months(date_range)

        df_result = None

        # Generate statement for each month and scrape it from the web site
        for month in months:
            check_txt = '{0} - {1}'.format(
                month[0].strftime('%Y-%m-%d'), month[1].strftime('%Y-%m-%d'))
            iuvo.generate_statement_direct(
                (month[0], month[1]), (By.ID, 'date_from'), (By.ID, 'date_to'),
                '%Y-%m-%d', EC.text_to_be_present_in_element(
                    (By.XPATH, xpaths['statement_check']), check_txt),
                (By.ID, 'account_statement_filters_btn'))

            # Read statement from page
            statement_table = driver.find_element_by_class_name(
                'table-responsive')
            # pd.read_html returns a list of one element
            df = pd.read_html(
                statement_table.get_attribute("innerHTML"), index_col=0)[0]
            # Transpose table to get the headers at the top
            df = df.T
            df['Datum'] = month[0].strftime('%d.%m.%Y')
            df.set_index('Datum', inplace=True)

            if df_result is None:
                df_result = df
            else:
                df_result = df_result.append(df, sort=False)

        df_result.to_csv('p2p_downloads/iuvo_statement.csv')

def open_selenium_grupeer(
        date_range: Tuple[datetime.date, datetime.date],
        credentials: Tuple[str, str]) -> None:
    """
    Generate and download the Grupeer account statement for given date range.

    Args:
        date_range (tuple(datetime.date, datetime.date)): date range
            (start_date, end_date) for which the account statements must
            be generated.
        credentials (tuple[str, str]): (username, password) for Iuvo.

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
            hover_locator=(By.XPATH, xpaths['logout_hover'])) as grupeer:

        grupeer.open_start_page(
            EC.element_to_be_clickable((By.NAME, 'email')))

        grupeer.log_into_page(
            'email', 'password', credentials,
            EC.element_to_be_clickable((By.LINK_TEXT, 'Meine Investments')))

        grupeer.open_account_statement_page(
            'Account Statement', (By.ID, 'from'))

        grupeer.generate_statement_direct(
            date_range, (By.ID, 'from'), (By.ID, 'to'), '%d.%m.%Y',
            wait_until=EC.text_to_be_present_in_element(
                (By.CLASS_NAME, 'balance-block'),
                'Bilanz geöffnet am '
                + str(date_range[0].strftime('%d.%m.%Y'))),
            submit_btn_locator=(By.NAME, 'submit'))

        grupeer.download_statement('Account statement.xlsx', 'excel', By.NAME)

def open_selenium_dofinance(
        date_range: Tuple[datetime.date, datetime.date],
        credentials: Tuple[str, str]) -> None:
    """
    Generate and download the Dofinance account statement for given date range.

    Args:
        date_range (tuple(datetime.date, datetime.date)): date range
            (start_date, end_date) for which the account statements must
            be generated.
        credentials (tuple[str, str]): (username, password) for DoFinance

    """
    urls = {
        'login': 'https://www.dofinance.eu/de/users/login',
        'logout': 'https://www.dofinance.eu/de/users/logout',
        'statement': 'https://www.dofinance.eu/de/users/statement'}
    default_file_name = 'Statement_{0} 00_00_00-{1} 23_59_59.xlsx'.format(
        date_range[0].strftime('%Y-%m-%d'), date_range[1].strftime('%Y-%m-%d'))

    with P2P('DoFinance', urls, EC.title_contains('Kreditvergabe Plattform')) \
            as dofinance:

        dofinance.open_start_page(
            EC.element_to_be_clickable((By.NAME, 'email')))

        dofinance.log_into_page(
            'email', 'password', credentials,
            EC.element_to_be_clickable((By.LINK_TEXT, 'TRANSAKTIONEN')))

        dofinance.open_account_statement_page(
            'Transaktionen', (By.ID, 'date-from'))

        dofinance.generate_statement_direct(
            date_range, (By.ID, 'date-from'), (By.ID, 'date-to'), '%d.%m.%Y',
            wait_until=EC.element_to_be_clickable((By.NAME, 'xls')))

        dofinance.download_statement(default_file_name, 'xls', By.NAME)

def open_selenium_twino(
        date_range: Tuple[datetime.date, datetime.date],
        credentials: Tuple[str, str]) -> None:
    """
    Generate and download the Twino account statement for given date range.

    Args:
        date_range (tuple(datetime.date, datetime.date)): date range
            (start_date, end_date) for which the account statements must
            be generated.
        credentials (tuple[str, str]): (username, password) for Twino

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
            logout_locator=(By.XPATH, xpaths['logout_btn'])) as twino:

        twino.open_start_page(
            EC.element_to_be_clickable((By.XPATH, xpaths['login_btn'])))

        twino.log_into_page(
            'email', 'login-password', credentials,
            EC.element_to_be_clickable((By.XPATH, xpaths['statement'])),
            login_locator=(By.XPATH, xpaths['login_btn']))

        twino.open_account_statement_page(
            'TWINO', (By.XPATH, xpaths['start_date']))

        twino.generate_statement_direct(
            date_range, (By.XPATH, xpaths['start_date']),
            (By.XPATH, xpaths['end_date']), '%d.%m.%Y',
            wait_until=EC.element_to_be_clickable(
                (By.CSS_SELECTOR, '.accStatement__pdf')))

        twino.download_statement(
            'account_statement_*.xlsx', '.accStatement__pdf', By.CSS_SELECTOR)
