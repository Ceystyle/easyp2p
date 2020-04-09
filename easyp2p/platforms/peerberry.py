# Copyright 2018-19 Niko Sandschneider

"""
Download and parse PeerBerry statement.

"""

from datetime import date
from typing import Optional, Tuple

import pandas as pd
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from easyp2p.p2p_parser import P2PParser
from easyp2p.p2p_platform import P2PPlatform
from easyp2p.p2p_signals import Signals
from easyp2p.p2p_webdriver import P2PWebDriver


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
        self.statement = statement_without_suffix + '.csv'
        self.signals = signals

    def download_statement(
            self, driver: P2PWebDriver, credentials: Tuple[str, str]) -> None:
        """
        Generate and download the PeerBerry account statement.

        Args:
            driver: Instance of P2PWebDriver class.
            credentials: Tuple (username, password) for PeerBerry.

        """
        urls = {
            'login': 'https://peerberry.com/en/login',
            'statement': 'https://peerberry.com/en/statement',
        }
        xpaths = {
            'statement_btn': (
                '/html/body/div[1]/div/div/div[2]/div[3]/div[2]/div/form/div'
                '/div[4]/button'),
            'start_calendar': (
                '//*[@id="app"]/div/div/div[2]/div[3]/div[2]/div/form/div'
                '/div[1]/div/div[1]/div/input'),
            'end_calendar': (
                '//*[@id="app"]/div/div/div[2]/div[3]/div[2]/div/form/div'
                '/div[1]/div/div[2]/div/input'),
        }

        with P2PPlatform(
                self.name, driver, urls,
                EC.element_to_be_clickable((By.NAME, 'email')),
                logout_locator=(By.CLASS_NAME, 'logout'),
                signals=self.signals) as peerberry:

            peerberry.log_into_page(
                'email', 'password', credentials,
                EC.element_to_be_clickable((By.LINK_TEXT, 'Statement')))

            # Close the cookie policy
            try:
                peerberry.driver.wait(EC.element_to_be_clickable(
                    (By.CLASS_NAME, 'close-icon'))).click()
            except NoSuchElementException:
                pass

            peerberry.open_account_statement_page((By.NAME, 'startDate'))

            # Create account statement for given date range
            month_locator = (By.CLASS_NAME, 'MuiTypography-body1')
            prev_month_locator = (
                By.CLASS_NAME, 'MuiPickersCalendarHeader-iconButton')
            calendar_locator = (
                (By.XPATH, xpaths['start_calendar']),
                (By.XPATH, xpaths['end_calendar']))
            peerberry.generate_statement_calendar(
                self.date_range, month_locator, prev_month_locator,
                (By.CLASS_NAME, 'MuiPickersDay-day'), calendar_locator,
                submit_btn_locator=(By.XPATH, xpaths['statement_btn']),
                offset=-250)

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
            'Amount of interest payment received': parser.INTEREST_PAYMENT,
            'Amount of principal payment received': parser.REDEMPTION_PAYMENT,
            'Deposit': parser.IN_OUT_PAYMENT,
            'Investment': parser.INVESTMENT_PAYMENT}
        rename_columns = {'Currency Id': parser.CURRENCY, 'Date': parser.DATE}

        unknown_cf_types = parser.run(
            '%Y-%m-%d', rename_columns, cashflow_types, 'Type', 'Amount')

        return parser.df, unknown_cf_types
