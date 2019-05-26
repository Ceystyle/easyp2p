# Copyright 2018-19 Niko Sandschneider

"""
Download and parse Estateguru statement.

"""

from datetime import date
from typing import Optional, Tuple

import pandas as pd
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from easyp2p.p2p_parser import P2PParser
from easyp2p.p2p_platform import P2PPlatform
from easyp2p.p2p_webdriver import P2PWebDriver


class Estateguru:

    """
    Contains methods for downloading/parsing Estateguru account statements.
    """

    def __init__(
            self, date_range: Tuple[date, date],
            statement_without_suffix: str) -> None:
        """
        Constructor of Estateguru class.

        Args:
            date_range: Date range (start_date, end_date) for which the account
                statements must be generated.
            statement_without_suffix: File name including path but without
                suffix where the account statement should be saved.

        """
        self.name = 'Estateguru'
        self.date_range = date_range
        self.statement = statement_without_suffix + '.csv'

    def download_statement(
            self, driver: P2PWebDriver, credentials: Tuple[str, str]) -> None:
        """
        Generate and download Estateguru account statement for given date range.

        Args:
            driver: Instance of P2PWebDriver class.
            credentials: Tuple (username, password) for Estateguru.

        """
        urls = {
            'login': 'https://estateguru.co/de/?switch=de',
            'logout': 'https://estateguru.co/portal/logout/index',
            'statement': 'https://estateguru.co/portal/portfolio/account',
        }
        xpaths = {
            'account_statement_check': (
                '/html/body/section/div/div/div/div[2]/section[1]/div/div'
                '/div[2]/div/form/div[2]/ul/li[5]/a'),
            'filter_btn': (
                '/html/body/section/div/div/div/div[2]/section[2]/div[1]'
                '/div[1]/button/span'),
            'select_btn': (
                '/html/body/section/div/div/div/div[2]/section[2]/div[1]'
                '/div[2]/button'),
            'submit_btn': (
                '/html/body/section/div/div/div/div[2]/section[2]/div[1]'
                '/div[3]/form/div[6]/div/div[3]/button'),
        }

        with P2PPlatform(
                self.name, driver, urls,
                EC.element_to_be_clickable((By.LINK_TEXT, 'Einloggen'))) \
                as estateguru:

            estateguru.log_into_page(
                'username', 'password', credentials,
                EC.element_to_be_clickable((By.LINK_TEXT, 'KONTOSTAND')),
                login_locator=(By.LINK_TEXT, 'Einloggen'))

            estateguru.open_account_statement_page(
                (By.XPATH, xpaths['filter_btn']))

            # Open the filter dialog and generate the statement
            estateguru.driver.find_element_by_xpath(
                xpaths['filter_btn']).click()
            estateguru.generate_statement_direct(
                self.date_range, (By.ID, 'dateApproveFilter'),
                (By.ID, 'dateApproveFilterTo'), '%d.%m.%Y',
                wait_until=EC.element_to_be_clickable(
                    (By.XPATH, xpaths['select_btn'])),
                submit_btn_locator=(By.XPATH, xpaths['submit_btn']))

            # Open the download dialog and download the statement
            estateguru.driver.find_element_by_xpath(
                xpaths['select_btn']).click()
            driver.wait(EC.element_to_be_clickable((By.LINK_TEXT, 'CSV')))
            estateguru.download_statement(
                self.statement, (By.LINK_TEXT, 'CSV'))

    def parse_statement(self, statement: Optional[str] = None) \
            -> Tuple[pd.DataFrame, str]:
        """
        Parser for Estateguru.

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
            self.name, self.date_range, self.statement, skipfooter=1)

        # Only consider valid cashflows
        parser.df = parser.df[parser.df['Cashflow-Status'] == 'Genehmigt']

        # Define mapping between Estateguru and easyp2p cashflow types and
        # column names
        cashflow_types = {
            # Treat bonus payments as normal interest payments
            'Bonus': parser.INTEREST_PAYMENT,
            'Einzahlung(Banktransfer)': parser.IN_OUT_PAYMENT,
            'Auszahlung(Banktransfer)': parser.IN_OUT_PAYMENT,
            'Entschädigung': parser.LATE_FEE_PAYMENT,
            'Hauptbetrag': parser.REDEMPTION_PAYMENT,
            'Investition(Auto Investieren)': parser.INVESTMENT_PAYMENT,
            'Strafe': parser.LATE_FEE_PAYMENT,
            'Zins': parser.INTEREST_PAYMENT}
        rename_columns = {
            'Cashflow-Typ': 'Estateguru_Cashflow-Typ',
            'Bestätigungsdatum': parser.DATE}

        unknown_cf_types = parser.run(
            '%d/%m/%Y %H:%M', rename_columns, cashflow_types,
            'Estateguru_Cashflow-Typ', 'Betrag', 'Verfügbar für Investitionen')

        return parser.df, unknown_cf_types
