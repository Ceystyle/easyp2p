#  Copyright (c) 2018-2020 Niko Sandschneider

"""
Download and parse PeerBerry statement.

"""

from datetime import date
from typing import Optional, Tuple

import pandas as pd
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from easyp2p.p2p_parser import P2PParser
from easyp2p.p2p_platform import P2PPlatform
from easyp2p.p2p_signals import Signals


class PeerBerry:

    """
    Contains methods for downloading/parsing PeerBerry account statements.
    """

    def __init__(
            self, date_range: Tuple[date, date],
            statement_without_suffix: str,
            signals: Optional[Signals] = None) -> None:
        """
        Constructor of PeerBerry class.

        Args:
            date_range: Date range (start_date, end_date) for which the account
                statements must be generated.
            statement_without_suffix: File name including path but without
                suffix where the account statement should be saved.
            signals: Signals instance for communicating with the calling class.

        """
        self.name = 'PeerBerry'
        self.date_range = date_range
        self.statement = statement_without_suffix + '.xlsx'
        self.signals = signals

    def download_statement(self, headless: bool) -> None:
        """
        Generate and download the PeerBerry account statement for given date
        range.

        Args:
            headless: If True use ChromeDriver in headless mode, if False not.

        """
        urls = {
            'login': 'https://peerberry.com/en/client/',
            'statement': 'https://peerberry.com/en/client/statement',
        }
        xpaths = {
            'statement_btn': (
                '/html/body/div[1]/div/div/div/div[2]/div[3]/div[2]/div/form'
                '/div/div[4]/button'),
        }

        with P2PPlatform(
                self.name, headless, urls,
                EC.element_to_be_clickable((By.NAME, 'email')),
                logout_locator=(By.CLASS_NAME, 'logout'),
                signals=self.signals) as peerberry:

            peerberry.log_into_page(
                'email', 'password',
                EC.element_to_be_clickable((By.LINK_TEXT, 'Statement')))

            # Close the cookie policy
            peerberry.driver.click_button(
                (By.CLASS_NAME, 'close-icon'), 'Ignored', raise_error=False)

            peerberry.open_account_statement_page((By.NAME, 'startDate'))

            # Create account statement for given date range
            month_locator = (By.CLASS_NAME, 'MuiTypography-body1')
            prev_month_locator = (
                By.CLASS_NAME, 'MuiPickersCalendarHeader-iconButton')
            start_calendar = ((By.NAME, 'startDate'), 1)
            end_calendar = ((By.NAME, 'endDate'), 1)
            peerberry.generate_statement_calendar(
                self.date_range, month_locator, prev_month_locator,
                (By.CLASS_NAME, 'MuiPickersDay-day'),
                start_calendar, end_calendar,
                submit_btn_locator=(By.XPATH, xpaths['statement_btn']))

            peerberry.download_statement(
                self.statement, (By.CLASS_NAME, 'download'))

    def parse_statement(self, statement: Optional[str] = None) \
            -> Tuple[pd.DataFrame, Tuple[str, ...]]:
        """
        Parser for Peerberry.

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
            self.name, self.date_range, self.statement, signals=self.signals)

        # Define mapping between PeerBerry and easyp2p cash flow types and
        # column names
        cashflow_types = {
            'BUYBACK_INTEREST': parser.BUYBACK_INTEREST_PAYMENT,
            'BUYBACK_PRINCIPAL': parser.BUYBACK_PAYMENT,
            'INVESTMENT': parser.INVESTMENT_PAYMENT,
            'REPAYMENT_INTEREST': parser.INTEREST_PAYMENT,
            'REPAYMENT_PRINCIPAL': parser.REDEMPTION_PAYMENT}
        rename_columns = {'Currency Id': parser.CURRENCY, 'Date': parser.DATE}

        unknown_cf_types = parser.run(
            '%Y-%m-%d', rename_columns, cashflow_types, 'Type', 'Amount')

        return parser.df, unknown_cf_types
