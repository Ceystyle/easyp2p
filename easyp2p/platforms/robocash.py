# -*- coding: utf-8 -*-
#  Copyright (c) 2018-2020 Niko Sandschneider

"""
Download and parse Robocash statement.

"""

from datetime import date
from typing import Optional, Tuple

import pandas as pd
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from PyQt5.QtCore import QCoreApplication

from easyp2p.p2p_parser import P2PParser
from easyp2p.p2p_platform import P2PPlatform
from easyp2p.p2p_signals import Signals

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
        self.signals = signals

    def download_statement(self, headless: bool) -> None:
        """
        Generate and download the Robocash account statement.

        Args:
            headless: If True use ChromeDriver in headless mode, if False not.

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
                self.name, headless, urls,
                EC.element_to_be_clickable((By.XPATH, xpaths['login_field'])),
                signals=self.signals) as robocash:

            robocash.log_into_page(
                'email', 'password',
                EC.element_to_be_clickable((By.LINK_TEXT, 'Account statement')),
                login_locator=(By.XPATH, xpaths['login_field']))

            robocash.open_account_statement_page((By.ID, 'new_statement'))

            # Open statement filter dialog
            robocash.driver.click_button(
                (By.ID, 'new_statement'),
                _translate(
                    'P2PPlatform',
                    f'{self.name}: starting account statement generation '
                    'failed!'),
                wait_until=EC.element_to_be_clickable((By.ID, 'date-after')))

            robocash.generate_statement_direct(
                self.date_range, (By.ID, 'date-after'),
                (By.ID, 'date-before'), '%Y-%m-%d')

            robocash.driver.wait_and_reload(
                urls['statement'],
                EC.element_to_be_clickable((By.ID, 'download_statement')),
                3, 45,
                _translate(
                    'P2PPlatform',
                    f'{self.name}: account statement generation took too '
                    f'long!'))

            robocash.download_statement(
                self.statement, (By.ID, 'download_statement'))

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
            'Withdrawal of funds': parser.IN_OUT_PAYMENT,
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
