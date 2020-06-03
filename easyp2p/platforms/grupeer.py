#  Copyright (c) 2018-2020 Niko Sandschneider

"""
Download and parse Grupeer statement.

"""

from typing import Optional, Tuple

import pandas as pd
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from easyp2p.p2p_parser import P2PParser
from easyp2p.p2p_platform import P2PPlatform
from easyp2p.platforms.base_platform import BasePlatform


class Grupeer(BasePlatform):

    """
    Contains methods for downloading/parsing Grupeer account statements.

    """

    NAME = 'Grupeer'
    SUFFIX = 'xlsx'
    DATE_FORMAT = '%d.%m.%Y'
    RENAME_COLUMNS = {
        'Date': P2PParser.DATE,
        'Currency': P2PParser.CURRENCY,
    }
    CASH_FLOW_TYPES = {
        # Treat cashback as interest payment:
        'Cashback': P2PParser.INTEREST_PAYMENT,
        'Deposit': P2PParser.IN_OUT_PAYMENT,
        'Withdrawal': P2PParser.IN_OUT_PAYMENT,
        'Interest': P2PParser.INTEREST_PAYMENT,
        'Investment': P2PParser.INVESTMENT_PAYMENT,
        'Principal': P2PParser.REDEMPTION_PAYMENT,
    }
    ORIG_CF_COLUMN = 'Type'
    VALUE_COLUMN = 'Amount'
    BALANCE_COLUMN = 'Balance'

    def download_statement(  # pylint: disable=arguments-differ
            self, headless: bool) -> None:
        """
        Generate and download the Grupeer account statement for given date
        range.

        Args:
            headless: If True use ChromeDriver in headless mode, if False not.

        """
        urls = {
            'login': 'https://www.grupeer.com/login',
            'statement': ('https://www.grupeer.com/account-statement'
                          '?currency_code=eur'),
        }

        with P2PPlatform(
                self.NAME, headless, urls,
                EC.element_to_be_clickable((By.LINK_TEXT, 'Sign In')),
                logout_locator=(By.LINK_TEXT, 'Logout'),
                hover_locator=(By.CLASS_NAME, 'header-auth-menu-name'),
                signals=self.signals) as grupeer:

            grupeer.log_into_page('email', 'password', None)
            grupeer.wait_for_captcha(
                (By.CLASS_NAME, 'text-danger'),
                'These credentials do not match our records.')

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
            self.NAME, self.date_range, self.statement, signals=self.signals)

        # Convert amount and balance to float64
        parser.df['Amount'] = parser.df['Amount'].apply(
            lambda x: x.replace(',', '.')).astype('float64')
        parser.df['Balance'] = parser.df['Balance'].apply(
            lambda x: x.replace(',', '.')).astype('float64')

        unknown_cf_types = parser.parse(
            self.DATE_FORMAT, self.RENAME_COLUMNS, self.CASH_FLOW_TYPES,
            self.ORIG_CF_COLUMN, self.VALUE_COLUMN, self.BALANCE_COLUMN)

        return parser.df, unknown_cf_types
