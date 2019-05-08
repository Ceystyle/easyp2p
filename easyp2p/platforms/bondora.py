# -*- coding: utf-8 -*-
# Copyright 2018-19 Niko Sandschneider

"""
Download and parse Bondora statement.

"""

from datetime import date
from typing import Optional, Tuple

import pandas as pd
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

from easyp2p.p2p_helper import nbr_to_short_month
from easyp2p.p2p_parser import P2PParser
from easyp2p.p2p_platform import P2PPlatform
from easyp2p.p2p_webdriver import (
    P2PWebDriver, one_of_many_expected_conditions_true)


class Bondora:

    """Contains methods for downloading/parsing Bondora account statements."""

    def __init__(
            self, date_range: Tuple[date, date],
            statement_without_suffix: str) -> None:
        """
        Constructor of Bondora class.

        Args:
            date_range: Date range (start_date, end_date) for which the account
                statements must be generated.
            statement_without_suffix: File name including path but without
                suffix where the account statement should be saved.

        """
        self.name = 'Bondora'
        self.date_range = date_range
        self.statement = statement_without_suffix + '.xlsx'

    def download_statement(
            self, driver: P2PWebDriver, credentials: Tuple[str, str]) -> None:
        """
        Generate and download the Bondora account statement.

        Args:
            driver: Instance of P2PWebDriver class.
            credentials: Tuple (username, password) for Bondora.

        """
        urls = {
            'login': 'https://www.bondora.com/de/login',
            'logout': 'https://www.bondora.com/de/authorize/logout',
            'statement': 'https://www.bondora.com/de/cashflow',
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

        with P2PPlatform(
                self.name, driver, urls,
                EC.element_to_be_clickable((By.NAME, 'Email'))) as bondora:

            bondora.log_into_page(
                'Email', 'Password', credentials,
                EC.element_to_be_clickable((By.LINK_TEXT, 'Cashflow')))

            bondora.open_account_statement_page((By.ID, 'StartYear'))

            # Change the date values to the given start and end dates
            start_month = nbr_to_short_month(self.date_range[0].strftime('%m'))
            end_month = nbr_to_short_month(self.date_range[1].strftime('%m'))
            select = Select(bondora.driver.find_element_by_id('StartYear'))
            select.select_by_visible_text(str(self.date_range[0].year))
            select = Select(bondora.driver.find_element_by_id('StartMonth'))
            select.select_by_visible_text(start_month)
            select = Select(bondora.driver.find_element_by_id('EndYear'))
            select.select_by_visible_text(str(self.date_range[1].year))
            select = Select(bondora.driver.find_element_by_id('EndMonth'))
            select.select_by_visible_text(end_month)

            # Start the account statement generation
            driver.find_element_by_xpath(xpaths['search_btn']).click()

            # Wait until statement generation is finished
            no_payments_msg = 'Keine Zahlungen gefunden'

            conditions = [
                EC.text_to_be_present_in_element(
                    (By.XPATH, xpaths['start_date']), '{0} {1}'.format(
                        start_month, self.date_range[0].year)),
                EC.text_to_be_present_in_element(
                    (By.XPATH, xpaths['no_payments']), no_payments_msg)]
            try:
                driver.wait(one_of_many_expected_conditions_true(conditions))
            except TimeoutException as err:
                raise TimeoutException(err)

            bondora.download_statement(
                self.statement, (By.XPATH, xpaths['download_btn']))

    def parse_statement(self, statement: Optional[str] = None) \
            -> Tuple[pd.DataFrame, str]:
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

        parser = P2PParser(self.name, self.date_range, self.statement)

        # Calculate defaulted payments
        parser.df[parser.DEFAULTS] = (
            parser.df['Erhaltener Kapitalbetrag - gesamt']
            - parser.df['Geplanter Kapitalbetrag - gesamt'])

        # Define mapping between Bondora and easyp2p column names
        rename_columns = {
            'Eingesetztes Kapital (netto)': parser.INCOMING_PAYMENT,
            'Endsaldo': parser.END_BALANCE_NAME,
            'Erhaltener Kapitalbetrag - gesamt': parser.REDEMPTION_PAYMENT,
            'Erhaltene Zinsen - gesamt': parser.INTEREST_PAYMENT,
            'Investitionen (netto)': parser.INVESTMENT_PAYMENT,
            'Startguthaben': parser.START_BALANCE_NAME,
            'Zeitraum': parser.DATE}

        unknown_cf_types = parser.start_parser(
            '%d.%m.%Y', rename_columns=rename_columns)

        return parser.df, unknown_cf_types
