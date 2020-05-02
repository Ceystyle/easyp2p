# -*- coding: utf-8 -*-
#  Copyright (c) 2018-2020 Niko Sandschneider

"""
Download and parse Bondora statement.

"""

from datetime import date
from typing import Optional, Tuple

import pandas as pd
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from easyp2p.p2p_parser import P2PParser
from easyp2p.p2p_platform import P2PPlatform
from easyp2p.p2p_signals import Signals
from easyp2p.p2p_webdriver import (
    P2PWebDriver, one_of_many_expected_conditions_true)


class Bondora:

    """Contains methods for downloading/parsing Bondora account statements."""

    def __init__(
            self, date_range: Tuple[date, date],
            statement_without_suffix: str,
            signals: Optional[Signals] = None) -> None:
        """
        Constructor of Bondora class.

        Args:
            date_range: Date range (start_date, end_date) for which the account
                statements must be generated.
            statement_without_suffix: File name including path but without
                suffix where the account statement should be saved.
            signals: Signals instance for communicating with the calling class.

        """
        self.name = 'Bondora'
        self.date_range = date_range
        self.statement = statement_without_suffix + '.xlsx'
        self.signals = signals

    def download_statement(
            self, headless: bool, credentials: Tuple[str, str]) -> None:
        """
        Generate and download the Bondora account statement for given date range.

        Args:
            headless: If True use ChromeDriver in headless mode, if False not.
            credentials: Tuple (username, password).

        """
        urls = {
            'login': 'https://www.bondora.com/en/login',
            'logout': 'https://www.bondora.com/en/authorize/logout',
            'statement': 'https://www.bondora.com/en/cashflow',
        }
        xpaths = {
            'no_payments': '/html/body/div[1]/div/div/div/div[3]/div',
            'search_btn': (
                '//*[@id="page-content-wrapper"]/div/div/div[1]/form/div[3]'
                '/button'),
            'start_date': (
                '/html/body/div[1]/div/div/div/div[3]/div/table/tbody/tr[2]'
                '/td[1]/a'),
            'download_btn': (
                '/html/body/div[1]/div/div/div/div[1]/form/div[4]/div/a'),
        }
        # Use a dict to handle nbr to short name conversion, so we do not
        # have to rely on English locale to be installed
        map_nbr_to_short_month = {
            '01': 'Jan', '02': 'Feb', '03': 'Mar', '04': 'Apr', '05': 'May',
            '06': 'Jun', '07': 'Jul', '08': 'Aug', '09': 'Sep', '10': 'Oct',
            '11': 'Nov', '12': 'Dec'}
        start_month = map_nbr_to_short_month[self.date_range[0].strftime('%m')]
        date_dict = {
            (By.ID, 'StartMonth'): start_month,
            (By.ID, 'StartYear'): str(self.date_range[0].year),
            (By.ID, 'EndMonth'): map_nbr_to_short_month[
                self.date_range[1].strftime('%m')],
            (By.ID, 'EndYear'): str(self.date_range[1].year)}
        no_payments_msg = 'Payments were not found in the selected period.'
        conditions = [
            EC.text_to_be_present_in_element(
                (By.XPATH, xpaths['start_date']),
                f'{start_month} {self.date_range[0].year}'),
            EC.text_to_be_present_in_element(
                (By.XPATH, xpaths['no_payments']), no_payments_msg)]

        with P2PPlatform(
                self.name, headless, urls,
                EC.element_to_be_clickable((By.NAME, 'Email')),
                signals=self.signals) as bondora:

            bondora.log_into_page(
                'Email', 'Password', credentials,
                EC.element_to_be_clickable((By.LINK_TEXT, 'Cash flow')))

            bondora.open_account_statement_page((By.ID, 'StartYear'))

            bondora.generate_statement_combo_boxes(
                date_dict, (By.XPATH, xpaths['search_btn']),
                one_of_many_expected_conditions_true(conditions))

            bondora.download_statement(
                self.statement, (By.XPATH, xpaths['download_btn']))

    def parse_statement(self, statement: Optional[str] = None) \
            -> Tuple[pd.DataFrame, Tuple[str, ...]]:
        """
        Parser for Bondora.

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

        # Calculate defaulted payments
        parser.df[parser.DEFAULTS] = (
            parser.df['Principal received - total']
            - parser.df['Principal planned - total'])

        # Define mapping between Bondora and easyp2p column names
        rename_columns = {
            'Net capital deployed': parser.IN_OUT_PAYMENT,
            'Closing balance': parser.END_BALANCE_NAME,
            'Principal received - total': parser.REDEMPTION_PAYMENT,
            'Interest received - total': parser.INTEREST_PAYMENT,
            'Net loan investments': parser.INVESTMENT_PAYMENT,
            'Opening balance': parser.START_BALANCE_NAME,
            'Period': parser.DATE}

        unknown_cf_types = parser.run('%d.%m.%Y', rename_columns=rename_columns)

        return parser.df, unknown_cf_types
