# Copyright 2018-19 Niko Sandschneider

"""
Download and parse Estateguru statement.

.. moduleauthor:: Niko Sandschneider <nsandschn@gmx.de>

"""

from datetime import date
import os
from typing import Tuple

import pandas as pd
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from easyp2p.p2p_parser import P2PParser
from easyp2p.p2p_platform import P2PPlatform


class Estateguru:

    def __init__(self, date_range: Tuple[date, date]) -> None:
        """
        Constructor of Estateguru class.

        Args:
            date_range: date range (start_date, end_date) for which the account
                statements must be generated

        """
        self.name = 'Estateguru'
        self.date_range = date_range

    def download_statement(self, credentials: Tuple[str, str]) -> None:
        """
        Generate and download Estateguru account statement for given date range.

        Args:
            credentials: (username, password) for Estateguru

        """
        urls = {
            'login': 'https://estateguru.co/de/?switch=de',
            'logout': 'https://estateguru.co/portal/logout/index',
            'statement': 'https://estateguru.co/portal/portfolio/account'}
        xpaths = {
            'account_statement_check': ('/html/body/section/div/div/div/div[2]/'
                                        'section[1]/div/div/div[2]/div/form/'
                                        'div[2]/ul/li[5]/a'),
            'select_btn': ('/html/body/section/div/div/div/div[2]/section[2]/'
                           'div[1]/div[2]/button')}
        default_file_name = 'payments_{0}*.csv'.format(
            date.today().strftime('%Y-%m-%d'))

        with P2PPlatform(
                'Estateguru', urls,
                EC.element_to_be_clickable((By.LINK_TEXT, 'Einloggen'))) \
                as estateguru:

            self.statement_file_name = estateguru.set_statement_file_name(
                self.date_range, 'csv')

            estateguru.log_into_page(
                'username', 'password', credentials,
                EC.element_to_be_clickable((By.LINK_TEXT, 'KONTOSTAND')),
                login_locator=(By.LINK_TEXT, 'Einloggen'))

            estateguru.open_account_statement_page(
                'Übersicht', (By.XPATH, xpaths['account_statement_check']))

            # Estateguru does not provide functionality for filtering payment
            # dates. Therefore we download the statement which includes all
            # cashflows ever generated for this account. That also means that
            # date_range is not used for Estateguru. We keep it as input
            # variable anyway to be consistent with the other platform classes.
            estateguru.driver.find_element_by_xpath(
                xpaths['select_btn']).click()
            estateguru.wdwait(EC.element_to_be_clickable((By.LINK_TEXT, 'CSV')))
            estateguru.download_statement(
                default_file_name, self.statement_file_name,
                (By.LINK_TEXT, 'CSV'))


    def parse_statement(self, statement_file_name: str = None) \
            -> Tuple[pd.DataFrame, str]:
        """
        Parser for Estateguru.

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
        elif not os.path.exists(self.statement_file_name):
            raise RuntimeError(
                'Kontoauszugsdatei {0} konnte nicht gefunden werden!'
                .format(self.statement_file_name))

        parser = P2PParser(self.name, self.date_range, self.statement_file_name)

        # Create a DataFrame with zero entries if there were no cashflows
        if parser.df.empty:
            parser.parse_statement()
            return (parser.df, '')

        # Drop last line which only contains a summary
        parser.df = parser.df[:-1]

        # Define mapping between Estateguru and easyP2P cashflow types and
        # column names
        cashflow_types = {
            # Treat bonus payments as normal interest payments
            'Bonus': parser.INTEREST_PAYMENT,
            'Einzahlung(Banktransfer)': parser.INCOMING_PAYMENT,
            'Entschädigung': parser.LATE_FEE_PAYMENT,
            'Hauptbetrag': parser.REDEMPTION_PAYMENT,
            'Investition(Auto Investieren)': parser.INVESTMENT_PAYMENT,
            'Zins': parser.INTEREST_PAYMENT}
        rename_columns = {
            'Cashflow-Typ': 'Estateguru_Cashflow-Typ',
            'Bestätigungsdatum': parser.DATE}

        unknown_cf_types = parser.parse_statement(
            '%d/%m/%Y %H:%M', rename_columns, cashflow_types,
            'Estateguru_Cashflow-Typ', 'Betrag', 'Verfügbar für Investitionen')

        return (parser.df, unknown_cf_types)
