# -*- coding: utf-8 -*-
# Copyright 2018-19 Niko Sandschneider

"""
Download and parse Twino statement.

"""

from datetime import date
from typing import Tuple

import pandas as pd
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

import easyp2p.p2p_helper as p2p_helper
from easyp2p.p2p_parser import P2PParser
from easyp2p.p2p_platform import P2PPlatform
from easyp2p.p2p_webdriver import PlatformWebDriver


class Twino:

    """
    Contains two public methods for downloading/parsing Twino account
    statements.

    """

    def __init__(self, date_range: Tuple[date, date]) -> None:
        """
        Constructor of Twino class.

        Args:
            date_range: date range (start_date, end_date) for which the account
                statements must be generated

        """
        self.name = 'Twino'
        self.date_range = date_range
        self.statement_file_name = p2p_helper.create_statement_location(
            self.name, self.date_range, 'xlsx')

    def download_statement(self, credentials: Tuple[str, str]) -> None:
        """
        Generate and download the Twino account statement for given date range.

        Args:
            credentials: (username, password) for Twino

        """
        urls = {
            'login': 'https://www.twino.eu/de/',
            'statement': ('https://www.twino.eu/de/profile/investor/'
                          'my-investments/account-transactions')}
        xpaths = {
            'end_date': '//*[@date-picker="filterData.processingDateTo"]',
            'login_btn': ('/html/body/div[1]/div[2]/div[1]/header[1]/div/nav/'
                          'div/div[1]/button'),
            'logout_btn': '//a[@href="/logout"]',
            'start_date': '//*[@date-picker="filterData.processingDateFrom"]',
            'statement': ('//a[@href="/de/profile/investor/my-investments/'
                          'individual-investments"]')}

        twino = P2PPlatform(self.name, urls, self.statement_file_name)

        with PlatformWebDriver(
            twino, EC.element_to_be_clickable((By.XPATH, xpaths['login_btn'])),
            logout_locator=(By.XPATH, xpaths['logout_btn'])):

            twino.log_into_page(
                'email', 'login-password', credentials,
                EC.element_to_be_clickable((By.XPATH, xpaths['statement'])),
                login_locator=(By.XPATH, xpaths['login_btn']))

            twino.open_account_statement_page(
                'TWINO', (By.XPATH, xpaths['start_date']))

            twino.generate_statement_direct(
                self.date_range, (By.XPATH, xpaths['start_date']),
                (By.XPATH, xpaths['end_date']), '%d.%m.%Y',
                wait_until=EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, '.accStatement__pdf')))

            twino.download_statement(
                'account_statement_*.xlsx',
                (By.CSS_SELECTOR, '.accStatement__pdf'))


    def parse_statement(self, statement_file_name: str = None) \
            -> Tuple[pd.DataFrame, str]:
        """
        Parser for Twino.

        Keyword Args:
            statement_file_name: File name including path of the account
                statement which should be parsed

        Returns:
            Tuple with two elements. The first
            element is the data frame containing the parsed results. The second
            element is a set containing all unknown cash flow types.

        """
        if statement_file_name is not None:
            self.statement_file_name = statement_file_name

        parser = P2PParser(self.name, self.date_range, self.statement_file_name)

        # Format the header of the table
        parser.df = parser.df[1:]  # First row only contains a generic header
        new_header = parser.df.iloc[0] # Get the new first row as header
        parser.df = parser.df[1:] # Remove the first row
        parser.df.columns = new_header # Set the new header

        # Create a DataFrame with zero entries if there were no cashflows
        if parser.df.empty:
            parser.start_parser()
            return (parser.df, '')

        # Create a new column for identifying cashflow types
        try:
            parser.df['Twino_Cashflow-Typ'] = parser.df['Type'] + ' ' \
                + parser.df['Description']
        except KeyError:
            raise RuntimeError(
                'Twino: Cashflowspalte nicht im Kontoauszug vorhanden!')

        # Define mapping between Twino and easyp2p cashflow types and column
        # names
        cashflow_types = {
            'BUYBACK INTEREST': parser.BUYBACK_INTEREST_PAYMENT,
            'BUYBACK PRINCIPAL': parser.BUYBACK_PAYMENT,
            'BUY_SHARES PRINCIPAL': parser.INVESTMENT_PAYMENT,
            'CURRENCY_FLUCTUATION INTEREST': parser.INTEREST_PAYMENT,
            'EXTENSION INTEREST': parser.INTEREST_PAYMENT,
            'REPAYMENT INTEREST': parser.INTEREST_PAYMENT,
            'REPAYMENT PRINCIPAL': parser.REDEMPTION_PAYMENT,
            'REPURCHASE INTEREST': parser.BUYBACK_INTEREST_PAYMENT,
            'REPURCHASE PRINCIPAL': parser.BUYBACK_PAYMENT,
            'SCHEDULE INTEREST': parser.INTEREST_PAYMENT
            }
        rename_columns = {'Processing Date': parser.DATE}

        unknown_cf_types = parser.start_parser(
            '%d.%m.%Y %H:%M', rename_columns, cashflow_types,
            'Twino_Cashflow-Typ', 'Amount, EUR')

        return (parser.df, unknown_cf_types)
