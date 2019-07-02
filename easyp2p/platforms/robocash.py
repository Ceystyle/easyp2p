# -*- coding: utf-8 -*-
# Copyright 2018-19 Niko Sandschneider

"""
Download and parse Robocash statement.

"""

from datetime import date
from typing import Optional, Tuple

import pandas as pd
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from PyQt5.QtCore import QCoreApplication

from easyp2p.p2p_parser import P2PParser
from easyp2p.p2p_platform import P2PPlatform
from easyp2p.p2p_signals import PlatformFailedError, Signals
from easyp2p.p2p_webdriver import P2PWebDriver

_translate = QCoreApplication.translate


class Robocash:

    """
    Contains methods for downloading/parsing Robocash account statements.
    """

    signals = Signals()

    def __init__(
            self, date_range: Tuple[date, date],
            statement_without_suffix: str,
            signals: Optional[Signals] = None) -> None:
        """
        Constructor of Robocash class.

        Args:
            date_range: Date range (start_date, end_date) for which the account
                statements must be generated.
            statement_without_suffix: File name including path but without
                suffix where the account statement should be saved.
            signals: Signals instance for communicating with the calling class.

        """
        self.name = 'Robocash'
        self.date_range = date_range
        self.statement = statement_without_suffix + '.xls'
        if signals:
            self.signals.connect_signals(signals)

    def download_statement(
            self, driver: P2PWebDriver, credentials: Tuple[str, str]) -> None:
        """
        Generate and download the Robocash account statement.

        Args:
            driver: Instance of P2PWebDriver class.
            credentials: Tuple (username, password) for Robocash.

        Raises:
            PlatformFailedError: If the statement button cannot be found
                          - If the download of the statement takes too long

        """
        urls = {
            'login': 'https://robo.cash/',
            'logout': 'https://robo.cash/logout',
            'statement': 'https://robo.cash/cabinet/statement',
        }
        xpaths = {
            'login_field': '/html/body/header/div/div[2]/a',
        }

        with P2PPlatform(
                self.name, driver, urls,
                EC.element_to_be_clickable((By.XPATH, xpaths['login_field'])),
                signals=self.signals) as robocash:

            robocash.log_into_page(
                'email', 'password', credentials,
                EC.element_to_be_clickable((By.LINK_TEXT, 'Account statement')),
                login_locator=(By.XPATH, xpaths['login_field']))

            robocash.open_account_statement_page((By.ID, 'new_statement'))

            try:
                statement_btn = driver.wait(EC.element_to_be_clickable(
                    (By.ID, 'new_statement')))
                statement_btn.click()
            except NoSuchElementException:
                self.signals.add_progress_text.emit(_translate(
                    'P2PPlatform', '{}: starting account statement generation '
                    'failed!').format(self.name), True)
                raise PlatformFailedError

            robocash.generate_statement_direct(
                self.date_range, (By.ID, 'date-after'),
                (By.ID, 'date-before'), '%Y-%m-%d')

            self._wait_for_statement(driver, urls['statement'])

            robocash.download_statement(
                self.statement, (By.ID, 'download_statement'))

    def _wait_for_statement(self, driver: P2PWebDriver, url: str) -> None:
        """
        Helper method to wait for successful statement generation.

        Robocash does not automatically show download button after
        statement generation is done. An explicit reload of the page is
        needed.

        Args:
            driver:
            url: URL of the account statement page.

        Raises:
            PlatformFailedError: If the account statement generation takes
                too long.

        """
        wait = 0
        self.signals.add_progress_text.emit(_translate(
            'P2PPlatform', 'Note: generating the Robocash account '
            'statement can take up to one minute!'), False)
        while True:
            try:
                driver.get(url)
                driver.wait(EC.element_to_be_clickable(
                    (By.ID, 'download_statement')))
                break
            except TimeoutException:
                wait += 1
                if wait > 15:  # Roughly 15 * delay seconds
                    self.signals.add_progress_text.emit(_translate(
                        'P2PPlatform',
                        '{}: account statement generation took too '
                        'long!').format(self.name), True)
                    raise PlatformFailedError

    def parse_statement(self, statement: Optional[str] = None) \
            -> Tuple[pd.DataFrame, Tuple[str, ...]]:
        """
        Parser for Robocash.

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

        # Define mapping between Robocash and easyp2p cash flow types and
        # column names
        cashflow_types = {
            'Adding funds': parser.IN_OUT_PAYMENT,
            'Paying interest': parser.INTEREST_PAYMENT,
            'Purchasing a loan': parser.INVESTMENT_PAYMENT,
            'Returning a loan': parser.REDEMPTION_PAYMENT,
            'Withdrawal of Funds': parser.IN_OUT_PAYMENT,
            # We don't report cash transfers within Robocash:
            'Creating a portfolio': parser.IGNORE,
            'Refilling a portfolio': parser.IGNORE,
            'Withdrawing from a portfolio': parser.IGNORE,
        }
        rename_columns = {'Date and time': parser.DATE}

        unknown_cf_types = parser.run(
            '%Y-%m-%d %H:%M:%S', rename_columns, cashflow_types,
            'Operation', 'Amount', "Portfolio's balance")

        return parser.df, unknown_cf_types
