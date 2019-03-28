# Copyright 2018-19 Niko Sandschneider

"""
Download and parse Grupeer statement.

.. moduleauthor:: Niko Sandschneider <nsandschn@gmx.de>

"""

from datetime import date
from typing import Tuple

import pandas as pd
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from easyp2p.p2p_parser import P2PParser
from easyp2p.p2p_platform import P2PPlatform


class Grupeer:

    def __init__(self, date_range: Tuple[date, date]) -> None:
        """
        Constructor of Grupeer class.

        Args:
            date_range: date range (start_date, end_date) for which the account
                statements must be generated

        """
        self.name = 'Grupeer'
        self.date_range = date_range

    def download_statement(self,  credentials: Tuple[str, str]) -> None:
        """
        Generate and download the Grupeer account statement.

        Args:
            credentials: (username, password) for Grupeer.

        """
        urls = {
            'login': 'https://www.grupeer.com/de/login',
            'statement': 'https://www.grupeer.com/de/account-statement'}
        xpaths = {
            'logout_hover': ('/html/body/div[4]/header/div/div/div[2]/div[1]/'
                             'div/div/ul/li/a/span')}

        with P2PPlatform(
                'Grupeer', urls,
                EC.element_to_be_clickable((By.LINK_TEXT, 'Einloggen')),
                (By.LINK_TEXT, 'Ausloggen'),
                hover_locator=(By.XPATH, xpaths['logout_hover'])) as grupeer:

            self.statement_file_name = grupeer.set_statement_file_name(
                self.date_range, 'xlsx')

            grupeer.log_into_page(
                'email', 'password', credentials,
                EC.element_to_be_clickable((By.LINK_TEXT, 'Meine Investments')))

            grupeer.open_account_statement_page(
                'Account Statement', (By.ID, 'from'))

            grupeer.generate_statement_direct(
                self.date_range, (By.ID, 'from'), (By.ID, 'to'), '%d.%m.%Y',
                wait_until=EC.text_to_be_present_in_element(
                    (By.CLASS_NAME, 'balance-block'),
                    'Bilanz geöffnet am '
                    + str(self.date_range[0].strftime('%d.%m.%Y'))),
                submit_btn_locator=(By.NAME, 'submit'))

            grupeer.download_statement(
                'Account statement*.xlsx', self.statement_file_name,
                (By.NAME, 'excel'))

    def parse_statement(self, statement_file_name: str = None) \
            -> Tuple[pd.DataFrame, str]:
        """
        Parser for Grupeer.

        Keyword Args:
            statement_file_name: File name including path of the account
                statement which should be parsed

        Returns:
            Tuple with two elements. The first
            element is the data frame containing the parsed results. The second
            element is a set containing all unknown cash flow types.

        """
        if statement_file_name is not None:
            self.statement_file_name = statement_file_name

        parser = P2PParser(self.name, self.date_range, self.statement_file_name)

        # Create a DataFrame with zero entries if there were no cashflows
        if parser.df.empty:
            parser.parse_statement()
            return (parser.df, '')

        # Get the currency from the Description column and replace known
        # currencies with their ISO code
        parser.df[parser.CURRENCY], parser.df['Details'] \
            = parser.df['Description'].str.split(';').str
        rename_currency = {'&euro': 'EUR', 'Gekauft &euro': 'EUR'}
        parser.df[parser.CURRENCY].replace(rename_currency, inplace=True)

        # Convert amount and balance to float64
        parser.df['Amount'] = parser.df['Amount'].apply(
            lambda x: x.replace(',', '.')).astype('float64')
        parser.df['Balance'] = parser.df['Balance'].apply(
            lambda x: x.replace(',', '.')).astype('float64')

        # Define mapping between Grupeer and easyp2p cashflow types and column
        # names
        cashflow_types = {
            # Treat cashback as interest payment:
            'Cashback': parser.INTEREST_PAYMENT,
            'Deposit': parser.INCOMING_PAYMENT,
            'Interest': parser.INTEREST_PAYMENT,
            'Investment': parser.INVESTMENT_PAYMENT,
            'Principal': parser.REDEMPTION_PAYMENT}
        rename_columns = {'Date': parser.DATE}

        unknown_cf_types = parser.parse_statement(
            '%d.%m.%Y', rename_columns, cashflow_types, 'Type', 'Amount',
            'Balance')

        return (parser.df, unknown_cf_types)
