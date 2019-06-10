# -*- coding: utf-8 -*-
# Copyright 2018-19 Niko Sandschneider

"""
Download and parse Twino statement.

"""

from datetime import date
from typing import Optional, Tuple

import pandas as pd
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from PyQt5.QtCore import QCoreApplication

from easyp2p.p2p_parser import P2PParser
from easyp2p.p2p_platform import P2PPlatform
from easyp2p.p2p_webdriver import P2PWebDriver

_translate = QCoreApplication.translate


class Twino:

    """
    Contains methods for downloading/parsing Twino account statements.
    """

    def __init__(
            self, date_range: Tuple[date, date],
            statement_without_suffix: str) -> None:
        """
        Constructor of Twino class.

        Args:
            date_range: Date range (start_date, end_date) for which the account
                statements must be generated.
            statement_without_suffix: File name including path but without
                suffix where the account statement should be saved.

        """
        self.name = 'Twino'
        self.date_range = date_range
        self.statement = statement_without_suffix + '.xlsx'

    def download_statement(
            self, driver: P2PWebDriver, credentials: Tuple[str, str]) -> None:
        """
        Generate and download the Twino account statement for given date range.

        Args:
            driver: Instance of P2PWebDriver class.
            credentials: Tuple (username, password) for Twino.

        """
        urls = {
            'login': 'https://www.twino.eu/en/',
            'statement': (
                'https://www.twino.eu/en/profile/investor/my-investments'
                '/account-transactions'),
        }
        xpaths = {
            'end_date': '//*[@date-picker="filterData.processingDateTo"]',
            'login_btn': (
                '/html/body/div[1]/div[2]/div[1]/header[1]/div/nav/div/div[1]'
                '/button'),
            'logout_btn': '//a[@href="/logout"]',
            'start_date': '//*[@date-picker="filterData.processingDateFrom"]',
            'statement': (
                '//a[@href="/en/profile/investor/my-investments/'
                'individual-investments"]'),
        }

        with P2PPlatform(
                self.name, driver, urls,
                EC.element_to_be_clickable((By.XPATH, xpaths['login_btn'])),
                logout_locator=(By.XPATH, xpaths['logout_btn'])) as twino:

            twino.log_into_page(
                'email', 'login-password', credentials,
                EC.element_to_be_clickable((By.XPATH, xpaths['statement'])),
                login_locator=(By.XPATH, xpaths['login_btn']))

            twino.open_account_statement_page((By.XPATH, xpaths['start_date']))

            twino.generate_statement_direct(
                self.date_range, (By.XPATH, xpaths['start_date']),
                (By.XPATH, xpaths['end_date']), '%d.%m.%Y',
                wait_until=EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, '.accStatement__pdf')))

            twino.download_statement(
                self.statement, (By.CSS_SELECTOR, '.accStatement__pdf'))

    def parse_statement(self, statement: Optional[str] = None) \
            -> Tuple[pd.DataFrame, str]:
        """
        Parser for Twino.

        Args:
            statement: File name including path of the account
                statement which should be parsed. If None, the file at
                self.statement will be parsed. Default is None.

        Returns:
            Tuple with two elements. The first element is the data frame
            containing the parsed results. The second element is a set
            containing all unknown cash flow types.

        """
        if statement:
            self.statement = statement

        parser = P2PParser(self.name, self.date_range, self.statement, header=2)

        # Create a new column for identifying cash flow types
        try:
            parser.df['Cash Flow Type'] = parser.df['Type'] + ' ' \
                + parser.df['Description']
        except KeyError as err:
            raise RuntimeError(_translate(
                'P2PParser',
                '{0}: column {1} is missing in account statement!').format(
                    self.name, str(err)))

        # Define mapping between Twino and easyp2p cash flow types and column
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

        unknown_cf_types = parser.run(
            '%d.%m.%Y %H:%M', rename_columns, cashflow_types,
            'Cash Flow Type', 'Amount, EUR')

        return parser.df, unknown_cf_types
