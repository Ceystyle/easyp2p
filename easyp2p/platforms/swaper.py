# -*- coding: utf-8 -*-
#  Copyright (c) 2018-2020 Niko Sandschneider

"""
Download and parse Swaper statement.

"""

from selenium.webdriver.common.by import By

from easyp2p.p2p_parser import P2PParser
from easyp2p.p2p_webdriver import P2PWebDriver
from easyp2p.platforms.base_platform import BasePlatform


class Swaper(BasePlatform):

    """
    Contains methods for downloading/parsing Swaper account statements.
    """

    NAME = 'Swaper'
    SUFFIX = 'xlsx'

    # Downloader settings
    DOWNLOAD_METHOD = 'webdriver'
    LOGIN_URL = 'https://www.swaper.com/#/dashboard'
    STATEMENT_URL = 'https://www.swaper.com/#/overview/account-statement'
    LOGOUT_WAIT_UNTIL_LOC = (By.ID, 'dashboard')
    LOGOUT_LOCATOR = (By.ID, 'logout')

    # Parser settings
    DATE_FORMAT = '%d.%m.%Y'
    RENAME_COLUMNS = {'Booking date': P2PParser.DATE}
    CASH_FLOW_TYPES = {
        'BUYBACK_INTEREST': P2PParser.BUYBACK_INTEREST_PAYMENT,
        'BUYBACK_PRINCIPAL': P2PParser.BUYBACK_PAYMENT,
        'EXTENSION_INTEREST': P2PParser.INTEREST_PAYMENT,
        'FUNDING': P2PParser.IN_OUT_PAYMENT,
        'INVESTMENT': P2PParser.INVESTMENT_PAYMENT,
        'REPAYMENT_INTEREST': P2PParser.INTEREST_PAYMENT,
        'REPAYMENT_PRINCIPAL': P2PParser.REDEMPTION_PAYMENT,
        'WITHDRAWAL': P2PParser.IN_OUT_PAYMENT,
    }
    ORIG_CF_COLUMN = 'Transaction type'
    VALUE_COLUMN = 'Amount'

    def _webdriver_download(self, webdriver: P2PWebDriver) -> None:
        """
        Generate and download the Swaper account statement for given date range.

        Args:
            webdriver: P2PWebDriver instance.

        """
        xpaths = {
            'day_table': (
                "//*[@class='datepicker opened']//*[@class='dates']//table"
                "//td"),
            'month': "//*[@class='datepicker opened']//*[@class='month']",
        }

        webdriver.log_into_page(
            self.LOGIN_URL, 'email', 'password', (By.ID, 'open-investments'))

        webdriver.open_account_statement_page(
            self.STATEMENT_URL, (By.ID, 'account-statement'))

        start_calendar = ((By.CLASS_NAME, 'datepicker-container'), 0)
        end_calendar = ((By.CLASS_NAME, 'datepicker-container'), 1)
        month_locator = (By.XPATH, xpaths['month'])
        prev_month_locator = (By.CSS_SELECTOR, '.opened .icon-left')

        webdriver.generate_statement_calendar(
            self.date_range, month_locator, prev_month_locator,
            (By.XPATH, xpaths['day_table']),
            start_calendar, end_calendar,
            day_class_check=(' ', ' selected'))

        webdriver.download_statement(
            self.statement, (By.CLASS_NAME, 'download-excel'))
