# Copyright 2018-19 Niko Sandschneider

"""
Download and parse Peerberry statement.

.. moduleauthor:: Niko Sandschneider <nsandschn@gmx.de>

"""

from datetime import date
from typing import Tuple

import pandas as pd
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException

from p2p_parser import P2PParser
from p2p_platform import P2PPlatform


def download_statement(
        date_range: Tuple[date, date],
        credentials: Tuple[str, str]) -> None:
    """
    Generate and download the PeerBerry account statement for given date range.

    Args:
        date_range (tuple(date, date)): date range
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

    with P2PPlatform(
            'PeerBerry', urls, EC.title_contains('Einloggen'),
            logout_locator=(By.XPATH, xpaths['logout_btn'])) as peerberry:

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
        default_dates = (date.today(), date.today())
        arrows = {'arrow_tag': 'th',
                  'left_arrow_class': 'rdtPrev',
                  'right_arrow_class': 'rdtNext'}
        calendar_locator = ((By.NAME, 'startDate'), (By.NAME, 'endDate'))
        days_table = {'class_name': 'rdtDays',
                      'current_day_id': 'rdtDay',
                      'id_from_calendar': False,
                      'table_id': 'class'}

        peerberry.generate_statement_calendar(
            date_range, default_dates, arrows, days_table, calendar_locator)

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
            'transactions*.csv', (By.XPATH, xpaths['download_btn']),
            actions='move_to_element')


def parse_statement(
        date_range: Tuple[date, date],
        input_file: str = 'p2p_downloads/peerberry_statement.csv') \
        -> Tuple[pd.DataFrame, str]:
    """
    Parser for Peerberry.

    Args:
        date_range (tuple(date, date)): date range
            (start_date, end_date) for which the investment results must be
            shown.

    Keyword Args:
        input_file (str): file name including path of the account statement
            downloaded from the PeerBerry web site

    Returns:
        tuple(pandas.DataFrame, set(str)): tuple with two elements. The first
        element is the data frame containing the parsed results. The second
        element is a set containing all unknown cash flow types.

    """
    parser = P2PParser('PeerBerry', date_range, input_file)

    # Create a DataFrame with zero entries if there were no cashflows
    if parser.df.empty:
        parser.parse_statement()
        return (parser.df, '')

    # Define mapping between PeerBerry and easyP2P cashflow types and column
    # names
    cashflow_types = {
        'Amount of interest payment received': parser.INTEREST_PAYMENT,
        'Amount of principal payment received': parser.REDEMPTION_PAYMENT,
        'Investment': parser.INVESTMENT_PAYMENT}
    rename_columns = {'Currency Id': parser.CURRENCY, 'Date': parser.DATE}

    unknown_cf_types = parser.parse_statement(
        '%Y-%m-%d', rename_columns, cashflow_types, 'Type', 'Amount')

    return (parser.df, unknown_cf_types)
