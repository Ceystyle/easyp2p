#  Copyright (c) 2018-2020 Niko Sandschneider

"""
Download and parse Estateguru statement.

"""

from datetime import date
import time
from typing import Optional, Tuple

import pandas as pd
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from PyQt5.QtCore import QCoreApplication

from easyp2p.p2p_parser import P2PParser
from easyp2p.p2p_platform import P2PPlatform
from easyp2p.p2p_signals import Signals
from easyp2p.p2p_webdriver import P2PWebDriver

_translate = QCoreApplication.translate


class Estateguru:

    """
    Contains methods for downloading/parsing Estateguru account statements.
    """

    def __init__(
            self, date_range: Tuple[date, date],
            statement_without_suffix: str,
            signals: Optional[Signals] = None) -> None:
        """
        Constructor of Estateguru class.

        Args:
            date_range: Date range (start_date, end_date) for which the account
                statements must be generated.
            statement_without_suffix: File name including path but without
                suffix where the account statement should be saved.
            signals: Signals instance for communicating with the calling class.

        """
        self.name = 'Estateguru'
        self.date_range = date_range
        self.statement = statement_without_suffix + '.csv'
        self.signals = signals

    def download_statement(
            self, driver: P2PWebDriver, credentials: Tuple[str, str]) -> None:
        """
        Generate and download Estateguru account statement for given date range.

        Args:
            driver: Instance of P2PWebDriver class.
            credentials: Tuple (username, password) for Estateguru.

        """
        urls = {
            'login': 'https://estateguru.co/?switch=en',
            'logout': 'https://estateguru.co/portal/logout/index',
            'statement': 'https://estateguru.co/portal/portfolio/account',
        }
        xpaths = {
            'account_statement_check': (
                '/html/body/section/div/div/div/div[2]/section[1]/div/div'
                '/div[2]/div/form/div[2]/ul/li[5]/a'),
            'download_btn': (
                '//*[@id="collapseTransactions"]/div/div/div[1]/div/div[2]'
                '/button'),
            'filter_btn': (
                '//*[@id="collapseTransactions"]/div/div/div[1]/div/div[1]'
                '/button'),
            'submit_btn': (
                '/html/body/section/div/div/div/div[2]/div/div/div/div/div[1]'
                '/div[3]/form/div[6]/div/div[3]/button')
        }

        with P2PPlatform(
                self.name, driver, urls,
                EC.element_to_be_clickable((By.LINK_TEXT, 'Log In')),
                signals=self.signals) as estateguru:

            estateguru.log_into_page(
                'username', 'password', credentials,
                EC.element_to_be_clickable((By.LINK_TEXT, 'ACCOUNT BALANCE')),
                login_locator=(By.LINK_TEXT, 'Log In'))

            estateguru.open_account_statement_page(
                (By.XPATH, xpaths['filter_btn']))

            # Open the filter dialog and generate the statement
            start_date_locator = (
                By.ID, 'filter_dateApproveFilterFrom_dataTableTransaction')
            end_date_locator = (
                By.ID, 'filter_dateApproveFilterTo_dataTableTransaction')
            estateguru.driver.click_button(
                (By.XPATH, xpaths['filter_btn']),
                _translate(
                    'P2PPlatform',
                    f'{self.name}: starting download of account statement '
                    f'failed!'),
                wait_until=EC.element_to_be_clickable(start_date_locator))

            estateguru.generate_statement_direct(
                self.date_range,
                start_date_locator, end_date_locator, '%d.%m.%Y',
                wait_until=EC.element_to_be_clickable(
                    (By.ID, 'btnFilterPMTable')),
                submit_btn_locator=(By.ID, 'btnFilterPMTable'))

            # Clicking the submit button will move the screen to the bottom of
            # the page. Move back to top again.
            try:
                estateguru.driver.find_element(By.TAG_NAME, 'body').send_keys(
                    Keys.HOME)
            except NoSuchElementException:
                pass

            # Estateguru needs a bit until the download button can be clicked
            # without closing the drop-down menu at once
            time.sleep(1)

            # Open the download dialog and download the statement
            estateguru.driver.click_button(
                (By.XPATH, xpaths['download_btn']),
                _translate(
                    'P2PPlatform',
                    f'{self.name}: starting download of account statement '
                    f'failed!'),
                wait_until=EC.element_to_be_clickable((By.LINK_TEXT, 'CSV')))

            estateguru.download_statement(
                self.statement, (By.LINK_TEXT, 'CSV'))

    def parse_statement(self, statement: Optional[str] = None) \
            -> Tuple[pd.DataFrame, Tuple[str, ...]]:
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
            self.name, self.date_range, self.statement, skipfooter=1,
            signals=self.signals)

        # Only consider valid cash flows
        parser.df = parser.df[parser.df['Cash Flow Status'] == 'Approved']

        # Define mapping between Estateguru and easyp2p cash flow types and
        # column names
        cashflow_types = {
            # Treat bonus payments as normal interest payments
            'Bonus': parser.INTEREST_PAYMENT,
            'Deposit': parser.IN_OUT_PAYMENT,
            'Withdrawal': parser.IN_OUT_PAYMENT,
            'Indemnity': parser.LATE_FEE_PAYMENT,
            'Principal': parser.REDEMPTION_PAYMENT,
            'Investment(Auto Invest)': parser.INVESTMENT_PAYMENT,
            'Penalty': parser.LATE_FEE_PAYMENT,
            'Interest': parser.INTEREST_PAYMENT}
        rename_columns = {
            'Cash Flow Type': 'EG Cash Flow Type',
            'Confirmation Date': parser.DATE}

        unknown_cf_types = parser.run(
            '%d/%m/%Y %H:%M', rename_columns, cashflow_types,
            'EG Cash Flow Type', 'Amount', 'Available to invest')

        return parser.df, unknown_cf_types
