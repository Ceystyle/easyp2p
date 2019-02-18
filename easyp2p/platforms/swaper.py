# Copyright 2018-19 Niko Sandschneider

"""
Download and parse Swaper statement.

.. moduleauthor:: Niko Sandschneider <nsandschn@gmx.de>

"""

from datetime import date
from typing import Tuple

import pandas as pd
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from p2p_parser import P2PParser
from p2p_platform import P2PPlatform


def download_statement(
        date_range: Tuple[date, date],
        credentials: Tuple[str, str]) -> None:
    """
    Generate and download the Swaper account statement for given date range.

    Args:
        date_range (tuple(date, date)): date range
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

    with P2PPlatform(
            'Swaper', urls, EC.presence_of_element_located((By.ID, 'about')),
            logout_locator=(By.XPATH, xpaths['logout_btn'])) as swaper:

        swaper.log_into_page(
            'email', 'password', credentials,
            EC.presence_of_element_located((By.ID, 'open-investments')),
            fill_delay=0.5)

        swaper.open_account_statement_page(
            'Swaper', (By.ID, 'account-statement'))

        # calendar_locator must be a tuple of locators, thus the , at the end
        calendar_locator = ((By.CLASS_NAME, 'datepicker-container'), )
        arrows = {'arrow_tag': 'div',
                  'left_arrow_class': 'icon icon icon-left',
                  'right_arrow_class': 'icon icon icon-right'}
        days_table = {'class_name': '',
                      'current_day_id': ' ',
                      'id_from_calendar': True,
                      'table_id': 'id'}
        default_dates = (date.today().replace(day=1), date.today())

        swaper.generate_statement_calendar(
            date_range, default_dates, arrows, days_table, calendar_locator)

        swaper.download_statement(
            'excel-storage*.xlsx', (By.XPATH, xpaths['download_btn']))


def parse_statement(
        date_range: Tuple[date, date],
        input_file: str = 'p2p_downloads/swaper_statement.xlsx') \
        -> Tuple[pd.DataFrame, str]:
    """
    Parser for Swaper.

    Args:
        date_range (tuple(date, date)): date range
            (start_date, end_date) for which the investment results must be
            shown.

    Keyword Args:
        input_file (str): file name including path of the account statement
            downloaded from the Swaper web site

    Returns:
        tuple(pandas.DataFrame, set(str)): tuple with two elements. The first
        element is the data frame containing the parsed results. The second
        element is a set containing all unknown cash flow types.

    """
    parser = P2PParser('Swaper', date_range, input_file)

    # Create a DataFrame with zero entries if there were no cashflows
    if parser.df.empty:
        parser.parse_statement()
        return (parser.df, '')

    # Define mapping between Swaper and easyP2P cashflow types and column names
    cashflow_types = {
        'BUYBACK_INTEREST': parser.BUYBACK_INTEREST_PAYMENT,
        'BUYBACK_PRINCIPAL': parser.BUYBACK_PAYMENT,
        'EXTENSION_INTEREST': parser.INTEREST_PAYMENT,
        'INVESTMENT': parser.INVESTMENT_PAYMENT,
        'REPAYMENT_INTEREST': parser.INTEREST_PAYMENT,
        'REPAYMENT_PRINCIPAL': parser.REDEMPTION_PAYMENT}
    rename_columns = {'Booking date': parser.DATE}

    unknown_cf_types = parser.parse_statement(
        '%d.%m.%Y', rename_columns, cashflow_types,
        'Transaction type', 'Amount')

    return (parser.df, unknown_cf_types)
