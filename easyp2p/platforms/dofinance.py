# -*- coding: utf-8 -*-
#  Copyright (c) 2018-2020 Niko Sandschneider

"""
Download and parse DoFinance statement.

"""

from datetime import date
from typing import Optional, Tuple

import pandas as pd
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from easyp2p.p2p_parser import P2PParser
from easyp2p.p2p_platform import P2PPlatform
from easyp2p.p2p_signals import Signals


class DoFinance:

    """
    Contains methods for downloading/parsing DoFinance account statements.
    """

    def __init__(
            self, date_range: Tuple[date, date], statement_without_suffix: str,
            signals: Optional[Signals] = None) -> None:
        """
        Constructor of DoFinance class.

        Args:
            date_range: Date range (start_date, end_date) for which the account
                statements must be generated.
            statement_without_suffix: File name including path but without
                suffix where the account statement should be saved.
            signals: Signals instance for communicating with the calling class.

        """
        self.name = 'DoFinance'
        self.date_range = date_range
        self.statement = statement_without_suffix + '.xlsx'
        self.signals = signals

    def download_statement(self, headless: bool) -> None:
        """
        Generate and download the DoFinance account statement for given date
        range.

        Args:
            headless: If True use ChromeDriver in headless mode, if False not.

        """
        urls = {
            'login': 'https://www.dofinance.eu/en/users/login',
            'logout': 'https://www.dofinance.eu/en/users/logout',
            'statement': 'https://www.dofinance.eu/en/users/statement',
        }

        with P2PPlatform(
                self.name, headless, urls,
                EC.element_to_be_clickable(
                    (By.XPATH, '//a[@href="/en/users/login"]')),
                signals=self.signals) as dofinance:

            dofinance.log_into_page(
                'email', 'password',
                EC.element_to_be_clickable((By.LINK_TEXT, 'TRANSACTIONS')))

            dofinance.open_account_statement_page((By.ID, 'date-from'))

            dofinance.generate_statement_direct(
                self.date_range, (By.ID, 'date-from'), (By.ID, 'date-to'),
                '%d.%m.%Y',
                wait_until=EC.element_to_be_clickable((By.NAME, 'xls')))

            dofinance.download_statement(
                self.statement, (By.NAME, 'xls'))

    def parse_statement(self, statement: Optional[str] = None) \
            -> Tuple[pd.DataFrame, Tuple[str, ...]]:
        """
        Parser for DoFinance.

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

        parser = P2PParser(
            self.name, self.date_range, self.statement, skipfooter=2,
            signals=self.signals)

        # Define mapping between DoFinance and easyp2p cash flow types and
        # column names
        cashflow_types = {
            'Withdrawal': parser.IN_OUT_PAYMENT,
            'Profit': parser.INTEREST_PAYMENT,
            # treat bonus payments as interest payments
            'Investor Bonus': parser.INTEREST_PAYMENT}

        for cf_type in parser.df['Transaction Type'].unique():
            if cf_type.startswith('Repayment'):
                cashflow_types[cf_type] = parser.REDEMPTION_PAYMENT
            elif cf_type.startswith('Investment'):
                cashflow_types[cf_type] = parser.INVESTMENT_PAYMENT
            elif cf_type.startswith('Funding'):
                cashflow_types[cf_type] = parser.IN_OUT_PAYMENT

        rename_columns = {'Processing Date': parser.DATE}

        unknown_cf_types = parser.run(
            '%d.%m.%Y', rename_columns, cashflow_types, 'Transaction Type',
            'Amount, €')

        return parser.df, unknown_cf_types
