# -*- coding: utf-8 -*-
# Copyright 2018-19 Niko Sandschneider

"""
Download and parse DoFinance statement.

"""

from datetime import date
from typing import Tuple

import pandas as pd
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

import easyp2p.p2p_helper as p2p_helper
from easyp2p.p2p_parser import P2PParser
from easyp2p.p2p_platform import P2PPlatform
from easyp2p.p2p_webdriver import P2PWebDriver


class DoFinance:

    """
    Contains methods for downloading/parsing DoFinance account statements.
    """

    def __init__(self, date_range: Tuple[date, date]) -> None:
        """
        Constructor of DoFinance class.

        Args:
            date_range: date range (start_date, end_date) for which the account
                statements must be generated

        """
        self.name = 'DoFinance'
        self.date_range = date_range
        self.statement_file_name = p2p_helper.create_statement_location(
            self.name, self.date_range, 'xlsx')

    def download_statement(
            self, driver: P2PWebDriver, credentials: Tuple[str, str]) -> None:
        """
        Generate and download the DoFinance account statement.

        Args:
            driver: Instance of P2PWebDriver class
            credentials: (username, password) for DoFinance

        """
        urls = {
            'login': 'https://www.dofinance.eu/de/users/login',
            'logout': 'https://www.dofinance.eu/de/users/logout',
            'statement': 'https://www.dofinance.eu/de/users/statement'}

        # TODO: do not rely on text in title for checking successful logout
        with P2PPlatform(
            self.name, driver, urls,
            EC.title_contains('Kreditvergabe Plattform')) as dofinance:

            dofinance.log_into_page(
                'email', 'password', credentials,
                EC.element_to_be_clickable((By.LINK_TEXT, 'TRANSAKTIONEN')))

            dofinance.open_account_statement_page((By.ID, 'date-from'))

            dofinance.generate_statement_direct(
                self.date_range, (By.ID, 'date-from'), (By.ID, 'date-to'),
                '%d.%m.%Y',
                wait_until=EC.element_to_be_clickable((By.NAME, 'xls')))

            dofinance.download_statement(
                self.statement_file_name, (By.NAME, 'xls'))


    def parse_statement(self, statement_file_name: str = None) \
            -> Tuple[pd.DataFrame, str]:
        """
        Parser for DoFinance.

        Keyword Args:
            statement_file_name: File name including path of the account
                statement which should be parsed

        Returns:
            Tuple with two elements. The first
            element is the data frame containing the parsed results. The second
            element is a set containing all unknown cash flow types.

        Raises:
            RuntimeError: if the statement file cannot be found

        """
        if statement_file_name is not None:
            self.statement_file_name = statement_file_name

        parser = P2PParser(self.name, self.date_range, self.statement_file_name)

        # Drop the last two rows which only contain a summary
        parser.df = parser.df[:-2]

        # Define mapping between DoFinance and easyp2p cashflow types and
        # column names
        cashflow_types = {
            'Abhebungen': parser.OUTGOING_PAYMENT,
            'Gewinn': parser.INTEREST_PAYMENT}

        for interest_rate in ['5%', '7%', '9%', '12%']:
            cashflow_types[
                'Rückzahlung\nRate: {0} Typ: automatisch'
                .format(interest_rate)] = parser.REDEMPTION_PAYMENT
            cashflow_types[
                'Anlage\nRate: {0} Typ: automatisch'.format(interest_rate)] \
                = parser.INVESTMENT_PAYMENT

        rename_columns = {'Bearbeitungsdatum': parser.DATE}

        unknown_cf_types = parser.start_parser(
            '%d.%m.%Y', rename_columns, cashflow_types, 'Art der Transaktion',
            'Betrag, €')

        return (parser.df, unknown_cf_types)
