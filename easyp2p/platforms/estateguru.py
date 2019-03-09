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

from p2p_parser import P2PParser
from p2p_platform import P2PPlatform


def download_statement(
        date_range: Tuple[date, date],
        credentials: Tuple[str, str]) -> None:
    """
    Generate and download Estateguru account statement for given date range.

    Args:
        date_range (tuple(date, date)): date range
            (start_date, end_date) for which the account statements must
            be generated.
        credentials (tuple[str, str]): (username, password) for Estateguru

    """
    urls = {
        'login': 'https://estateguru.co/de/?switch=de',
        'logout': 'https://estateguru.co/portal/logout/index',
        'statement': 'https://estateguru.co/portal/portfolio/account'}
    xpaths = {
        'account_statement_check': ('/html/body/section/div/div/div/div[2]/'
                                    'section[1]/div/div/div[2]/div/form/'
                                    'div[2]/ul/li[5]/a'),
        'select_btn': ('/html/body/section/div/div/div/div[2]/section[2]/'
                       'div[1]/div[2]/button')}
    default_file_name = 'payments_{0}*.csv'.format(
        date.today().strftime('%Y-%m-%d'))

    with P2PPlatform(
            'Estateguru', urls,
            EC.element_to_be_clickable((By.LINK_TEXT, 'Einloggen'))) \
            as estateguru:

        estateguru.log_into_page(
            'username', 'password', credentials,
            EC.element_to_be_clickable((By.LINK_TEXT, 'KONTOSTAND')),
            login_locator=(By.LINK_TEXT, 'Einloggen'))

        estateguru.open_account_statement_page(
            'Übersicht', (By.XPATH, xpaths['account_statement_check']))

        # Estateguru does not provide functionality for filtering payment
        # dates. Therefore we download the statement which includes all
        # cashflows ever generated for this account. That also means that
        # date_range is not used for Estateguru. We keep it as input variable
        # anyway to be consistent with the other open_selenium_* functions.
        estateguru.driver.find_element_by_xpath(xpaths['select_btn']).click()
        estateguru.wdwait(EC.element_to_be_clickable((By.LINK_TEXT, 'CSV')))
        estateguru.download_statement(default_file_name, (By.LINK_TEXT, 'CSV'))


def parse_statement(
        date_range: Tuple[date, date],
        input_file: str = 'p2p_downloads/estateguru_statement.csv') \
        -> Tuple[pd.DataFrame, str]:
    """
    Parser for Estateguru.

    Args:
        date_range (tuple(date, date)): date range
            (start_date, end_date) for which the investment results must be
            shown.

    Keyword Args:
        input_file (str): file name including path of the account statement
            downloaded from the Estateguru web site

    Returns:
        tuple(pandas.DataFrame, set(str)): tuple with two elements. The first
        element is the data frame containing the parsed results. The second
        element is a set containing all unknown cash flow types.

    """
    parser = P2PParser('Estateguru', date_range, input_file)

    # Create a DataFrame with zero entries if there were no cashflows
    if parser.df.empty:
        parser.parse_statement()
        return (parser.df, '')

    # Drop last line which only contains a summary
    parser.df = parser.df[:-1]

    # Define mapping between Estateguru and easyP2P cashflow types and column
    # names
    cashflow_types = {
        # Treat bonus payments as normal interest payments
        'Bonus': parser.INTEREST_PAYMENT,
        'Einzahlung(Banktransfer)': parser.INCOMING_PAYMENT,
        'Entschädigung': parser.LATE_FEE_PAYMENT,
        'Hauptbetrag': parser.REDEMPTION_PAYMENT,
        'Investition(Auto Investieren)': parser.INVESTMENT_PAYMENT,
        'Zins': parser.INTEREST_PAYMENT}
    rename_columns = {
        'Cashflow-Typ': 'Estateguru_Cashflow-Typ',
        'Zahlungsdatum': parser.DATE}

    unknown_cf_types = parser.parse_statement(
        '%d/%m/%Y %H:%M', rename_columns, cashflow_types,
        'Estateguru_Cashflow-Typ', 'Betrag',  'Verfügbar für Investitionen')

    return (parser.df, unknown_cf_types)
