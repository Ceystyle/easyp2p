# -*- coding: utf-8 -*-
# Copyright 2018-19 Niko Sandschneider

"""
Download and parse Robocash statement.

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
    Generate and download the Robocash account statement for given date range.

    Args:
        date_range (tuple(date, date)): date range
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

    with P2PPlatform('Robocash', urls, EC.title_contains('Willkommen')) \
            as robocash:

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
        # name is not known like for the other P2PPlatform sites. For now we
        # use a generic * wildcard to find the file. This will not be safe
        # anymore as soon as parallel downloads to the p2p_downloads
        # directory are allowed. Thus:
        #TODO: find a safer method for downloading the Robocash statement
        robocash.download_statement('*', (By.ID, 'download_statement'))


def parse_statement(
        date_range: Tuple[date, date],
        input_file: str = 'p2p_downloads/robocash_statement.xls') \
        -> Tuple[pd.DataFrame, str]:
    """
    Parser for Robocash.

    Args:
        date_range (tuple(date, date)): date range
            (start_date, end_date) for which the investment results must be
            shown.

    Keyword Args:
        input_file (str): file name including path of the account statement
            downloaded from the Robocash web site

    Returns:
        tuple(pandas.DataFrame, set(str)): tuple with two elements. The first
        element is the data frame containing the parsed results. The second
        element is a set containing all unknown cash flow types.

    """
    parser = P2PParser('Robocash', date_range, input_file)

    # Create a DataFrame with zero entries if there were no cashflows
    if parser.df.empty:
        parser.parse_statement()
        return (parser.df, '')

    # Define mapping between Robocash and easyP2P cashflow types and
    # column names
    cashflow_types = {
        'Darlehenskauf': parser.INVESTMENT_PAYMENT,
        'Die Geldauszahlung': parser.OUTGOING_PAYMENT,
        'Geldeinzahlung': parser.INCOMING_PAYMENT,
        'Kreditrückzahlung': parser.REDEMPTION_PAYMENT,
        # We don't report cash transfers within Robocash:
        'Portfolio auffüllen': parser.IGNORE,
        'Zinsenzahlung': parser.INTEREST_PAYMENT}
    rename_columns = {'Datum und Laufzeit': parser.DATE}

    unknown_cf_types = parser.parse_statement(
        '%Y-%m-%d %H:%M:%S', rename_columns, cashflow_types,
        'Operation', 'Betrag', 'Der Saldo des Portfolios')

    return (parser.df, unknown_cf_types)
