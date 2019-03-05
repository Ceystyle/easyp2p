# -*- coding: utf-8 -*-
# Copyright 2018-19 Niko Sandschneider

"""
Download and parse Bondora statement.

.. moduleauthor:: Niko Sandschneider <nsandschn@gmx.de>

"""

from datetime import date
from typing import Tuple

import pandas as pd
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

from p2p_parser import P2PParser
from p2p_platform import P2PPlatform


def download_statement(
        date_range: Tuple[date, date],
        credentials: Tuple[str, str]) -> None:
    """
    Generate and download the Mintos account statement for given date range.

    Args:
        date_range (tuple(date, date)): date range
            (start_date, end_date) for which the account statements must
            be generated.
        credentials (tuple[str, str]): (username, password) for Mintos

    """
    urls = {
        'login': 'https://www.mintos.com/de/login',
        'statement': 'https://www.mintos.com/de/kontoauszug/'}
    xpaths = {
        'logout_btn': "//a[contains(@href,'logout')]"}
    default_file_name = '{0}-account-statement*.xlsx'.format(
        date.today().strftime('%Y%m%d'))

    with P2PPlatform(
            'Mintos', urls, EC.title_contains('Vielen Dank'),
            logout_locator=(By.XPATH, xpaths['logout_btn'])) as mintos:

        driver = mintos.driver
        mintos.log_into_page(
            '_username', '_password', credentials,
            EC.element_to_be_clickable((By.LINK_TEXT, 'Kontoauszug')))

        mintos.open_account_statement_page(
            'Account Statement', (By.ID, 'period-from'))

        mintos.generate_statement_direct(
            date_range, (By.ID, 'period-from'),
            (By.ID, 'period-to'), '%d.%m.%Y',
            submit_btn_locator=(By.ID, 'filter-button'))

        # If there were no cashflows in date_range, the download button will
        # not appear. In that case test if there really were no cashflows by
        # checking that there are only two lines in the account statement with
        # start and end balance of 0. If that is the case write an empty
        # DataFrame to the file.
        try:
            mintos.wdwait(
                EC.presence_of_element_located((By.ID, 'export-button')))
        except TimeoutException:
            try:
                cashflow_table = driver.find_element_by_id('overview-results')
                df = pd.read_html(cashflow_table.get_attribute("innerHTML"))[0]
            except ValueError:
                raise RuntimeError(
                    'Der Mintos-Kontoauszug konnte nicht erfolgreich '
                    'generiert werden')

            if len(df) == 2:
                if df.iloc[0][0] == 'Anfangssaldo ' \
                        + date_range[0].strftime('%d.%m.%Y') \
                    and df.iloc[0][1] == 0 \
                    and df.iloc[1][0] == 'Endsaldo ' \
                        + date_range[1].strftime('%d.%m.%Y'):
                    df = pd.DataFrame()
                    df.to_excel('p2p_downloads/mintos_statement.xlsx')
            else:
                raise RuntimeError(
                    'Der Mintos-Kontoauszug konnte nicht erfolgreich '
                    'generiert werden')
        else:
            mintos.download_statement(
                default_file_name, (By.ID, 'export-button'))


def parse_statement(
        date_range: Tuple[date, date],
        input_file: str = 'p2p_downloads/mintos_statement.xlsx') \
        -> Tuple[pd.DataFrame, str]:
    """
    Parser for Mintos.

    Args:
        date_range (tuple(date, date)): date range
            (start_date, end_date) for which the investment results must be
            shown.

    Keyword Args:
        input_file (str): file name including path of the account statement
            downloaded from the Mintos web site

    Returns:
        tuple(pandas.DataFrame, set(str)): tuple with two elements. The first
        element is the data frame containing the parsed results. The second
        element is a set containing all unknown cash flow types.

    """
    parser = P2PParser('Mintos', date_range, input_file)

    # Create a DataFrame with zero entries if there were no cashflows
    if parser.df.empty:
        parser.parse_statement()
        return (parser.df, '')

    try:
        # Create new columns for identifying cashflow types
        parser.df['Mintos_Cashflow-Typ'], parser.df['Loan ID'] = \
            parser.df['Details'].str.split(' Loan ID: ').str
        parser.df['Mintos_Cashflow-Typ'] = \
            parser.df['Mintos_Cashflow-Typ'].str.split(' Rebuy purpose').str[0]
    except KeyError as err:
        raise RuntimeError('Mintos: unbekannte Spalte im Parser: ' + str(err))

    # Define mapping between Mintos and easyP2P cashflow types and column names
    cashflow_types = {
        # Treat bonus/cashback payments as normal interest payments:
        'Cashback bonus': parser.INTEREST_PAYMENT,
        'Delayed interest income on rebuy': parser.BUYBACK_INTEREST_PAYMENT,
        'Interest income': parser.INTEREST_PAYMENT,
        'Interest income on rebuy': parser.BUYBACK_INTEREST_PAYMENT,
        'Investment principal rebuy': parser.BUYBACK_PAYMENT,
        'Investment principal increase': parser.INVESTMENT_PAYMENT,
        'Investment principal repayment': parser.REDEMPTION_PAYMENT,
        'Incoming client payment': parser.INCOMING_PAYMENT,
        'Late payment fee income': parser.LATE_FEE_PAYMENT,
        'Reversed incoming client payment': parser.OUTGOING_PAYMENT}
    rename_columns = {'Currency': parser.CURRENCY, 'Date': parser.DATE}

    unknown_cf_types = parser.parse_statement(
        '%Y-%m-%d %H:%M:%S', rename_columns, cashflow_types,
        'Mintos_Cashflow-Typ', 'Turnover', 'Balance')

    return (parser.df, unknown_cf_types)
