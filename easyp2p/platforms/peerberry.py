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
from selenium.common.exceptions import TimeoutException

from easyp2p.p2p_parser import P2PParser
from easyp2p.p2p_platform import P2PPlatform
from easyp2p.p2p_webdriver import P2PWebDriver


class PeerBerry:

    """
    Contains methods for downloading/parsing PeerBerry account statements.
    """

    def __init__(
            self, date_range: Tuple[date, date],
            statement_without_suffix: str) -> None:
        """
        Constructor of PeerBerry class.

        Args:
            date_range: Date range (start_date, end_date) for which the account
                statements must be generated.
            statement_without_suffix: File name including path but without
                suffix where the account statement should be saved.

        """
        self.name = 'PeerBerry'
        self.date_range = date_range
        self.statement = statement_without_suffix + '.csv'

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
            'cookie_policy': '//*[@id="app"]/div/div/div/div[4]/div/div/div[1]',
            'download_btn': (
                '//*[@id="app"]/div/div/div/div[2]/div/div[2]/div[3]/div[2]'
                '/div'),
            'login_btn': (
                '/html/body/div[1]/div/div/div/div[2]/div/div/div/div[1]/div'
                '/div/form/input'),
            'logout_btn': (
                '//*[@id="app"]/div/div/div/div[1]/div[1]/div/div/div[2]/div'),
            'start_balance': (
                '/html/body/div[1]/div/div/div/div[2]/div/div[2]/div[2]/div'
                '/div/div[1]'),
            'statement_btn': (
                '/html/body/div[1]/div/div/div/div[2]/div/div[2]/div[1]/div'
                '/div[2]/div/div[2]/div/span'),
        }

        with P2PPlatform(
                self.name, driver, urls,
                EC.element_to_be_clickable((By.XPATH, xpaths['login_btn'])),
                logout_locator=(By.XPATH, xpaths['logout_btn'])) as peerberry:

            peerberry.log_into_page(
                'email', 'password', credentials,
                EC.element_to_be_clickable((By.LINK_TEXT, 'Statement')))

            peerberry.open_account_statement_page((By.NAME, 'startDate'))

            # Close the cookie policy, if present
            try:
                driver.find_element_by_xpath(xpaths['cookie_policy']).click()
            except NoSuchElementException:
                pass

            # Create account statement for given date range
            default_dates = (date.today(), date.today())
            arrows = {
                'arrow_tag': 'th',
                'left_arrow_class': 'rdtPrev',
                'right_arrow_class': 'rdtNext',
            }
            calendar_locator = ((By.NAME, 'startDate'), (By.NAME, 'endDate'))
            days_table = {
                'class_name': 'rdtDays',
                'current_day_id': 'rdtDay',
                'id_from_calendar': False,
                'table_id': 'class'
            }

            peerberry.generate_statement_calendar(
                self.date_range, default_dates, arrows, days_table,
                calendar_locator,
                wait_until=EC.text_to_be_present_in_element(
                    (By.XPATH, xpaths['start_balance']),
                    'Opening balance '+str(self.date_range[0]).format(
                        '%Y-%m-%d')),
                submit_btn_locator=(By.XPATH, xpaths['statement_btn']))

            peerberry.download_statement(
                self.statement, (By.XPATH, xpaths['download_btn']),
                actions='move_to_element')

    def parse_statement(self, statement: Optional[str] = None) \
            -> Tuple[pd.DataFrame, str]:
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

        parser = P2PParser(self.name, self.date_range, self.statement)

        # Define mapping between PeerBerry and easyp2p cash flow types and
        # column names
        cashflow_types = {
            'Amount of interest payment received': parser.INTEREST_PAYMENT,
            'Amount of principal payment received': parser.REDEMPTION_PAYMENT,
            'Investment': parser.INVESTMENT_PAYMENT}
        rename_columns = {'Currency Id': parser.CURRENCY, 'Date': parser.DATE}

        unknown_cf_types = parser.run(
            '%Y-%m-%d', rename_columns, cashflow_types, 'Type', 'Amount')

        return parser.df, unknown_cf_types
