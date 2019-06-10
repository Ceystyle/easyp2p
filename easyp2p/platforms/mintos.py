# -*- coding: utf-8 -*-
# Copyright 2018-19 Niko Sandschneider

"""
Download and parse Mintos statement.

"""

from datetime import date
from typing import Optional, Tuple

import pandas as pd
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from PyQt5.QtCore import QCoreApplication

from easyp2p.p2p_parser import P2PParser
from easyp2p.p2p_platform import P2PPlatform
from easyp2p.p2p_webdriver import P2PWebDriver

_translate = QCoreApplication.translate


class Mintos:
    """
    Contains methods for downloading/parsing Mintos account statements.
    """

    def __init__(
            self, date_range: Tuple[date, date],
            statement_without_suffix: str) -> None:
        """
        Constructor of Mintos class.

        Args:
            date_range: Date range (start_date, end_date) for which the account
                statements must be generated.
            statement_without_suffix: File name including path but without
                suffix where the account statement should be saved.

        """
        self.name = 'Mintos'
        self.date_range = date_range
        self.statement = statement_without_suffix + '.xlsx'

    def download_statement(
            self, driver: P2PWebDriver, credentials: Tuple[str, str]) -> None:
        """
        Generate and download the Mintos account statement for given date range.

        Args:
            driver: Instance of P2PWebDriver class.
            credentials: Tuple (username, password) for Mintos.

        """
        urls = {
            'login': 'https://www.mintos.com/en/login',
            'statement': 'https://www.mintos.com/en/account-statement/'}
        xpaths = {
            'logout_btn': "//a[contains(@href,'logout')]"}

        with P2PPlatform(
                self.name, driver, urls,
                EC.element_to_be_clickable((By.ID, 'header-login-button')),
                logout_locator=(By.XPATH, xpaths['logout_btn'])) as mintos:

            mintos.log_into_page(
                '_username', '_password', credentials,
                EC.element_to_be_clickable((By.LINK_TEXT, 'Account Statement')))

            mintos.open_account_statement_page((By.ID, 'period-from'))

            mintos.generate_statement_direct(
                self.date_range, (By.ID, 'period-from'),
                (By.ID, 'period-to'), '%d.%m.%Y',
                submit_btn_locator=(By.ID, 'filter-button'))

            # If there were no cashflows in date_range, the download button will
            # not appear. In that case test if there really were no cashflows.
            # If that is the case write an empty DataFrame to the file.
            try:
                driver.wait(
                    EC.presence_of_element_located((By.ID, 'export-button')))
            except TimeoutException:
                try:
                    cashflow_table = driver.find_element_by_id(
                        'overview-results')
                    df = pd.read_html(
                        cashflow_table.get_attribute("innerHTML"))[0]

                    if self._no_cashflows(df):
                        df = pd.DataFrame()
                        df.to_excel(self.statement)
                    else:
                        raise ValueError
                except ValueError:
                    raise RuntimeError(_translate(
                        'P2PPlatform',
                        '{}: account statement generation failed!').format(
                            self.name))
            else:
                mintos.download_statement(
                    self.statement, (By.ID, 'export-button'))

    def _no_cashflows(self, df: pd.DataFrame) -> bool:
        """
        Helper method to determine if there were any cashflows in date_range.

        If there were no cashflows the Mintos cashflow table contains just two
        lines with start and end balance equal to zero.

        Args:
            df: DataFrame containing the Mintos cashflow table.

        Returns:
            True if there were no cashflows, False otherwise.

        """
        if len(df) != 2:
            return False

        if df.iloc[0][0] != (
                'Opening balance ' + self.date_range[0].strftime('%d.%m.%Y')):
            return False

        # Start balance value
        if df.iloc[0][1] != 0:
            return False

        if df.iloc[1][0] != (
                'Closing balance ' + self.date_range[1].strftime('%d.%m.%Y')):
            return False

        return True

    def parse_statement(self, statement: Optional[str] = None) \
            -> Tuple[pd.DataFrame, str]:
        """
        Parser for Mintos.

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

        parser = P2PParser(self.name, self.date_range, self.statement)

        try:
            # Create new columns for identifying cashflow types
            parser.df['Cash Flow Type'], parser.df['Loan ID'] = \
                parser.df['Details'].str.split(' Loan ID: ').str
            parser.df['Cash Flow Type'] = \
                parser.df['Cash Flow Type'].str.split(
                    ' Rebuy purpose').str[0]
        except (KeyError, ValueError):
            pass

        # Define mapping between Mintos and easyp2p cashflow types and column
        # names
        cashflow_types = {
            # Treat bonus/cashback payments as normal interest payments:
            'Cashback bonus': parser.INTEREST_PAYMENT,
            'Delayed interest income on rebuy': parser.BUYBACK_INTEREST_PAYMENT,
            'Interest income': parser.INTEREST_PAYMENT,
            'Interest income on rebuy': parser.BUYBACK_INTEREST_PAYMENT,
            'Investment principal rebuy': parser.BUYBACK_PAYMENT,
            'Investment principal increase': parser.INVESTMENT_PAYMENT,
            'Investment principal repayment': parser.REDEMPTION_PAYMENT,
            'Incoming client payment': parser.IN_OUT_PAYMENT,
            'Outgoing client payment': parser.IN_OUT_PAYMENT,
            'Late payment fee income': parser.LATE_FEE_PAYMENT,
            'Reversed incoming client payment': parser.IN_OUT_PAYMENT}
        rename_columns = {'Currency': parser.CURRENCY, 'Date': parser.DATE}

        unknown_cf_types = parser.run(
            '%Y-%m-%d %H:%M:%S', rename_columns, cashflow_types,
            'Cash Flow Type', 'Turnover', 'Balance')

        return parser.df, unknown_cf_types
