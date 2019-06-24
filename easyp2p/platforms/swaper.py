# -*- coding: utf-8 -*-
# Copyright 2018-19 Niko Sandschneider

"""
Download and parse Swaper statement.

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


class Swaper:

    """
    Contains methods for downloading/parsing Swaper account statements.
    """

    def __init__(
            self, date_range: Tuple[date, date],
            statement_without_suffix: str,
            signals: Optional[Signals] = None) -> None:
        """
        Constructor of Swaper class.

        Args:
            date_range: Date range (start_date, end_date) for which the account
                statements must be generated.
            statement_without_suffix: File name including path but without
                suffix where the account statement should be saved.
            signals: Signals instance for communicating with the calling class.

        """
        self.name = 'Swaper'
        self.date_range = date_range
        self.statement = statement_without_suffix + '.xlsx'
        self.signals = signals

    def download_statement(
            self, driver: P2PWebDriver, credentials: Tuple[str, str]) -> None:
        """
        Generate and download the Swaper account statement for given date range.

        Args:
            driver: Instance of P2PWebDriver class.
            credentials: (username, password) for Swaper.

        """
        urls = {
            'login': 'https://www.swaper.com/#/dashboard',
            'statement': 'https://www.swaper.com/#/overview/account-statement',
        }
        xpaths = {
            'download_btn': (
                '//*[@id="account-statement"]/div[3]/div[4]/div/div[1]/a'
                '/div[1]/div/span[2]'),
            'logout_btn': '//*[@id="logout"]/span[1]/span'
        }

        with P2PPlatform(
                self.name, driver, urls,
                EC.presence_of_element_located((By.ID, 'about')),
                logout_locator=(By.XPATH, xpaths['logout_btn']),
                signals=self.signals) as swaper:

            swaper.log_into_page(
                'email', 'password', credentials,
                EC.presence_of_element_located((By.ID, 'open-investments')),
                fill_delay=0.1)

            swaper.open_account_statement_page((By.ID, 'account-statement'))

            # calendar_locator must be tuple of locators, thus the , at the end
            calendar_locator = ((By.CLASS_NAME, 'datepicker-container'), )
            arrows = {'arrow_tag': 'div',
                      'left_arrow_class': 'icon icon icon-left',
                      'right_arrow_class': 'icon icon icon-right'}
            days_table = {'class_name': '',
                          'current_day_id': ' ',
                          'id_from_calendar': True,
                          'table_id': 'id'}
            default_dates = (date.today().replace(day=1), date.today())

            swaper.generate_statement_calendar(
                self.date_range, default_dates, arrows, days_table,
                calendar_locator)

            swaper.download_statement(
                self.statement, (By.XPATH, xpaths['download_btn']))

    def parse_statement(self, statement: Optional[str] = None) \
            -> Tuple[pd.DataFrame, str]:
        """
        Parser for Swaper.

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

        # Define mapping between Swaper and easyp2p cash flow types and column
        # names
        cashflow_types = {
            'BUYBACK_INTEREST': parser.BUYBACK_INTEREST_PAYMENT,
            'BUYBACK_PRINCIPAL': parser.BUYBACK_PAYMENT,
            'EXTENSION_INTEREST': parser.INTEREST_PAYMENT,
            'INVESTMENT': parser.INVESTMENT_PAYMENT,
            'REPAYMENT_INTEREST': parser.INTEREST_PAYMENT,
            'REPAYMENT_PRINCIPAL': parser.REDEMPTION_PAYMENT,
            'WITHDRAWAL': parser.IN_OUT_PAYMENT}
        rename_columns = {'Booking date': parser.DATE}

        unknown_cf_types = parser.run(
            '%d.%m.%Y', rename_columns, cashflow_types,
            'Transaction type', 'Amount')

        return parser.df, unknown_cf_types
