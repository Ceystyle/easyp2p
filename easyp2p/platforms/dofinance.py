# -*- coding: utf-8 -*-
# Copyright 2018-19 Niko Sandschneider

"""
Download and parse DoFinance statement.

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
    Generate and download the Dofinance account statement for given date range.

    Args:
        date_range (tuple(date, date)): date range
            (start_date, end_date) for which the account statements must
            be generated.
        credentials (tuple[str, str]): (username, password) for DoFinance

    """
    urls = {
        'login': 'https://www.dofinance.eu/de/users/login',
        'logout': 'https://www.dofinance.eu/de/users/logout',
        'statement': 'https://www.dofinance.eu/de/users/statement'}
    default_file_name = 'Statement_{0} 00_00_00-{1} 23_59_59*.xlsx'.format(
        date_range[0].strftime('%Y-%m-%d'), date_range[1].strftime('%Y-%m-%d'))

    with P2PPlatform(
            'DoFinance', urls, EC.title_contains('Kreditvergabe Plattform')) \
            as dofinance:

        dofinance.log_into_page(
            'email', 'password', credentials,
            EC.element_to_be_clickable((By.LINK_TEXT, 'TRANSAKTIONEN')))

        dofinance.open_account_statement_page(
            'Transaktionen', (By.ID, 'date-from'))

        dofinance.generate_statement_direct(
            date_range, (By.ID, 'date-from'), (By.ID, 'date-to'), '%d.%m.%Y',
            wait_until=EC.element_to_be_clickable((By.NAME, 'xls')))

        dofinance.download_statement(default_file_name, (By.NAME, 'xls'))


def parse_statement(
        date_range: Tuple[date, date],
        input_file: str = 'p2p_downloads/dofinance_statement.xlsx') \
        -> Tuple[pd.DataFrame, str]:
    """
    Parser for DoFinance.

    Args:
        date_range (tuple(date, date)): date range
            (start_date, end_date) for which the investment results must be
            shown.

    Keyword Args:
        input_file (str): file name including path of the account statement
            downloaded from the DoFinance web site

    Returns:
        tuple(pandas.DataFrame, set(str)): tuple with two elements. The first
        element is the data frame containing the parsed results. The second
        element is a set containing all unknown cash flow types.

    """
    parser = P2PParser('DoFinance', date_range, input_file)

    # Create a DataFrame with zero entries if there were no cashflows
    if parser.df.empty:
        parser.parse_statement()
        return (parser.df, '')

    # Drop the last two rows which only contain a summary
    parser.df = parser.df[:-2]

    # Define mapping between DoFinance and easyP2P cashflow types and column
    # names
    cashflow_types = {
        'Abhebungen': parser.OUTGOING_PAYMENT,
        'Gewinn': parser.INTEREST_PAYMENT}

    for interest_rate in ['5%', '7%', '9%', '12%']:
        cashflow_types[
            'Rückzahlung\nRate: {0} Typ: automatisch'.format(interest_rate)] \
            = parser.REDEMPTION_PAYMENT
        cashflow_types[
            'Anlage\nRate: {0} Typ: automatisch'.format(interest_rate)] \
            = parser.INVESTMENT_PAYMENT

    rename_columns = {'Bearbeitungsdatum': parser.DATE}

    unknown_cf_types = parser.parse_statement(
        '%d.%m.%Y', rename_columns, cashflow_types, 'Art der Transaktion',
        'Betrag, €')

    return (parser.df, unknown_cf_types)
