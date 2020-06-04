# -*- coding: utf-8 -*-
#  Copyright (c) 2018-2020 Niko Sandschneider

"""
Download and parse Mintos statement.

"""

import pandas as pd
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from PyQt5.QtCore import QCoreApplication

from easyp2p.p2p_parser import P2PParser
from easyp2p.p2p_platform import P2PPlatform
from easyp2p.p2p_signals import Signals
from easyp2p.p2p_chrome import P2PChrome
from easyp2p.platforms.base_platform import BasePlatform

_translate = QCoreApplication.translate


class Mintos(BasePlatform):
    """
    Contains methods for downloading/parsing Mintos account statements.
    """

    NAME = 'Mintos'
    SUFFIX = 'xlsx'
    DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    RENAME_COLUMNS = {
        'Currency': P2PParser.CURRENCY,
        'Date': P2PParser.DATE,
    }
    CASH_FLOW_TYPES = {
        'interest received': P2PParser.INTEREST_PAYMENT,
        'principal received': P2PParser.REDEMPTION_PAYMENT,
        'buyback: Principal received': P2PParser.BUYBACK_PAYMENT,
        'buyback: late payment interest received':
            P2PParser.BUYBACK_INTEREST_PAYMENT,
        'buyback: interest received': P2PParser.BUYBACK_INTEREST_PAYMENT,
        'loan agreement amended: Principal received':
            P2PParser.REDEMPTION_PAYMENT,
        'loan agreement amended: interest received':
            P2PParser.INTEREST_PAYMENT,
        'loan agreement extended: Principal received':
            P2PParser.REDEMPTION_PAYMENT,
        'loan agreement extended: interest received':
            P2PParser.INTEREST_PAYMENT,
        'investment in loan': P2PParser.INVESTMENT_PAYMENT,
        'early repayment of a loan: Principal received':
            P2PParser.REDEMPTION_PAYMENT,
        'early repayment of a loan: interest received':
            P2PParser.INTEREST_PAYMENT,
        'loan agreement extended: late payment interest received':
            P2PParser.INTEREST_PAYMENT,
        'late fees received': P2PParser.LATE_FEE_PAYMENT,
        'loan agreement amended: late payment interest received':
            P2PParser.INTEREST_PAYMENT,
        'early repayment of a loan: late payment interest received':
            P2PParser.INTEREST_PAYMENT,
        'other: Principal received': P2PParser.REDEMPTION_PAYMENT,
        'other: interest received': P2PParser.INTEREST_PAYMENT,
        'loan agreement terminated: Principal received':
            P2PParser.REDEMPTION_PAYMENT,
        'loan agreement terminated: interest received':
            P2PParser.INTEREST_PAYMENT,
        'loan agreement terminated: late payment interest received':
            P2PParser.INTEREST_PAYMENT,
        'other: late payment interest received': P2PParser.INTEREST_PAYMENT,
    }
    ORIG_CF_COLUMN = 'Cash Flow Type'
    VALUE_COLUMN = 'Turnover'
    BALANCE_COLUMN = 'Balance'

    signals = Signals()

    def download_statement(  # pylint: disable=arguments-differ
            self, headless: bool) -> None:
        """
        Generate and download the Mintos account statement for given date range.

        Args:
            headless: If True use ChromeDriver in headless mode, if False not.

        """
        urls = {
            'login': 'https://www.mintos.com/en/login',
            'statement': 'https://www.mintos.com/en/account-statement/'}
        xpaths = {
            'logout_btn': "//a[contains(@href,'logout')]"}

        with P2PPlatform(
                self.NAME, headless, urls,
                EC.element_to_be_clickable((By.ID, 'header-login-button')),
                logout_locator=(By.XPATH, xpaths['logout_btn']),
                signals=self.signals) as mintos:

            mintos.log_into_page('_username', '_password', None)
            mintos.wait_for_captcha(
                (By.CLASS_NAME, 'account-login-error'),
                'Invalid username or password')

            mintos.open_account_statement_page((By.ID, 'period-from'))

            mintos.generate_statement_direct(
                self.date_range, (By.ID, 'period-from'),
                (By.ID, 'period-to'), '%d.%m.%Y',
                submit_btn_locator=(By.ID, 'filter-button'))

            # If there were no cash flows in date_range, the download button
            # will not appear. In that case test if there really were no cash
            # flows. If true write an empty DataFrame to the file.
            try:
                mintos.driver.wait(
                    EC.presence_of_element_located((By.ID, 'export-button')))
            except TimeoutException:
                self._create_empty_statement(mintos.driver)
            else:
                mintos.download_statement(
                    self.statement, (By.ID, 'export-button'))

    @signals.update_progress
    def _create_empty_statement(self, driver: P2PChrome):
        try:
            cashflow_table = driver.find_element(By.ID, 'overview-results')
            df = pd.read_html(cashflow_table.get_attribute("innerHTML"))[0]

            if self._no_cashflows(df):
                df = pd.DataFrame()
                df.to_excel(self.statement)
            else:
                raise ValueError
        except (NoSuchElementException, ValueError):
            raise RuntimeError(_translate(
                'P2PPlatform',
                f'{self.NAME}: account statement generation failed!'))

    def _no_cashflows(self, df: pd.DataFrame) -> bool:
        """
        Helper method to determine if there were any cash flows in date_range.

        If there were no cash flows the Mintos cash flow table contains just
        two lines with start and end balance.

        Args:
            df: DataFrame containing the Mintos cash flow table.

        Returns:
            True if there were no cash flows, False otherwise.

        """
        if len(df) != 2:
            return False

        if df.iloc[0][0] != (
                'Opening balance ' + self.date_range[0].strftime('%d.%m.%Y')):
            return False

        if df.iloc[1][0] != (
                'Closing balance ' + self.date_range[1].strftime('%d.%m.%Y')):
            return False

        return True

    def _transform_df(self, parser: P2PParser) -> None:
        """
        Split the Details column into Loan ID and Cash Flow Type columns.

        Args:
            parser: P2PParser instance

        """
        detail_col = 'Details'
        parser.check_columns(detail_col)
        if parser.df.shape[0] > 0:
            parser.df['Loan ID'], parser.df['Cash Flow Type'] = \
                parser.df[detail_col].str.split(' - ').str
