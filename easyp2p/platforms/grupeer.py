#  Copyright (c) 2018-2020 Niko Sandschneider

"""
Download and parse Grupeer statement.

"""

from datetime import date
from typing import Optional, Tuple

import pandas as pd
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from easyp2p.p2p_parser import P2PParser
from easyp2p.p2p_platform import P2PPlatform
from easyp2p.p2p_signals import Signals
from easyp2p.p2p_webdriver import P2PWebDriver


class Grupeer:

    """
    Contains methods for downloading/parsing Grupeer account statements.

    """

    def __init__(
            self, date_range: Tuple[date, date],
            statement_without_suffix: str,
            signals: Optional[Signals] = None) -> None:
        """
        Constructor of Grupeer class.

        Args:
            date_range: Date range (start_date, end_date) for which the account
                statements must be generated.
            statement_without_suffix: File name including path but without
                suffix where the account statement should be saved.
            signals: Signals instance for communicating with the calling class.

        """
        self.name = 'Grupeer'
        self.date_range = date_range
        self.statement = statement_without_suffix + '.xlsx'
        self.signals = signals

    def download_statement(
            self, headless: bool, credentials: Tuple[str, str]) -> None:
        """
        Generate and download the Grupeer account statement for given date
        range.

        Args:
            headless: If True use ChromeDriver in headless mode, if False not.
            credentials: Tuple (username, password).

        """
        urls = {
            'login': 'https://www.grupeer.com/login',
            'statement': ('https://www.grupeer.com/account-statement'
                          '?currency_code=eur'),
        }

        with P2PPlatform(
                self.name, headless, urls,
                EC.element_to_be_clickable((By.LINK_TEXT, 'Sign In')),
                logout_locator=(By.LINK_TEXT, 'Logout'),
                hover_locator=(By.CLASS_NAME, 'header-auth-menu-name'),
                signals=self.signals) as grupeer:

            grupeer.log_into_page(
                'email', 'password', credentials,
                EC.element_to_be_clickable((By.LINK_TEXT, 'My Investments')))

            grupeer.open_account_statement_page((By.ID, 'from'))

            grupeer.generate_statement_direct(
                self.date_range, (By.ID, 'from'), (By.ID, 'to'), '%d.%m.%Y',
                wait_until=EC.text_to_be_present_in_element(
                    (By.CLASS_NAME, 'balance-block'),
                    'Starting balance on '
                    + str(self.date_range[0].strftime('%d.%m.%Y'))),
                submit_btn_locator=(By.NAME, 'submit'))

            grupeer.download_statement(self.statement, (By.NAME, 'excel'))

    def parse_statement(self, statement: Optional[str] = None) \
            -> Tuple[pd.DataFrame, Tuple[str, ...]]:
        """
        Parser for Grupeer.

        Args:
            statement: File name including path of the account statement which
                should be parsed. If None, the file at self.statement will be
                parsed. Default is None.

        Returns:
            Tuple with two elements. The first element is the data frame
            containing the parsed results. The second element is a set
            containing all unknown cash flow types.

        """
        if statement:
            self.statement = statement

        parser = P2PParser(
            self.name, self.date_range, self.statement, signals=self.signals)

        # Convert amount and balance to float64
        parser.df['Amount'] = parser.df['Amount'].apply(
            lambda x: x.replace(',', '.')).astype('float64')
        parser.df['Balance'] = parser.df['Balance'].apply(
            lambda x: x.replace(',', '.')).astype('float64')

        # Define mapping between Grupeer and easyp2p cash flow types and column
        # names
        cashflow_types = {
            # Treat cashback as interest payment:
            'Cashback': parser.INTEREST_PAYMENT,
            'Deposit': parser.IN_OUT_PAYMENT,
            'Withdrawal': parser.IN_OUT_PAYMENT,
            'Interest': parser.INTEREST_PAYMENT,
            'Investment': parser.INVESTMENT_PAYMENT,
            'Principal': parser.REDEMPTION_PAYMENT}
        rename_columns = {'Date': parser.DATE, 'Currency': parser.CURRENCY}

        unknown_cf_types = parser.run(
            '%d.%m.%Y', rename_columns, cashflow_types, 'Type', 'Amount',
            'Balance')

        return parser.df, unknown_cf_types
