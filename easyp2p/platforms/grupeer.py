#  Copyright (c) 2018-2020 Niko Sandschneider

"""
Download and parse Grupeer statement.

"""

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from easyp2p.p2p_parser import P2PParser
from easyp2p.p2p_webdriver import P2PWebDriver
from easyp2p.platforms.base_platform import BasePlatform


class Grupeer(BasePlatform):

    """
    Contains methods for downloading/parsing Grupeer account statements.

    """

    NAME = 'Grupeer'
    SUFFIX = 'xlsx'

    # Downloader settings
    DOWNLOAD_METHOD = 'recaptcha'
    LOGIN_URL = 'https://www.grupeer.com/login'
    STATEMENT_URL = \
        'https://www.grupeer.com/account-statement?currency_code=eur'
    LOGOUT_WAIT_UNTIL_LOC = (By.LINK_TEXT, 'Sign In')
    LOGOUT_LOCATOR = (By.LINK_TEXT, 'Logout')
    HOVER_LOCATOR = (By.CLASS_NAME, 'header-auth-menu-name')

    # Parser settings
    DATE_FORMAT = '%d.%m.%Y'
    RENAME_COLUMNS = {
        'Date': P2PParser.DATE,
        'Currency': P2PParser.CURRENCY,
    }
    CASH_FLOW_TYPES = {
        'Cashback': P2PParser.BONUS_PAYMENT,
        'Deposit': P2PParser.IN_OUT_PAYMENT,
        'Withdrawal': P2PParser.IN_OUT_PAYMENT,
        'Interest': P2PParser.INTEREST_PAYMENT,
        'Investment': P2PParser.INVESTMENT_PAYMENT,
        'Principal': P2PParser.REDEMPTION_PAYMENT,
    }
    ORIG_CF_COLUMN = 'Type'
    VALUE_COLUMN = 'Amount'
    BALANCE_COLUMN = 'Balance'

    def _webdriver_download(self, webdriver: P2PWebDriver) -> None:
        """
        Generate and download the Grupeer account statement for given date
        range.

        Args:
            webdriver: P2PWebDriver instance.

        """
        webdriver.log_into_page(self.LOGIN_URL, 'email', 'password', None)
        webdriver.wait_for_captcha(
            self.LOGIN_URL, (By.CLASS_NAME, 'text-danger'),
            'These credentials do not match our records.')

        webdriver.open_account_statement_page(
            self.STATEMENT_URL, (By.ID, 'from'))

        webdriver.generate_statement_direct(
            self.date_range, (By.ID, 'from'), (By.ID, 'to'), '%d.%m.%Y',
            wait_until=EC.text_to_be_present_in_element(
                (By.CLASS_NAME, 'balance-block'),
                'Starting balance on '
                + str(self.date_range[0].strftime('%d.%m.%Y'))),
            submit_btn_locator=(By.NAME, 'submit'))

        webdriver.download_statement(self.statement, (By.NAME, 'excel'))

    def _transform_df(self, parser: P2PParser) -> None:
        """
        Transform amount columns into floats.

        Args:
            parser: P2PParser instance.

        """
        parser.df[self.VALUE_COLUMN] = parser.df[self.VALUE_COLUMN].apply(
            lambda x: x.replace(',', '.')).astype('float64')
        parser.df[self.BALANCE_COLUMN] = parser.df[self.BALANCE_COLUMN].apply(
            lambda x: x.replace(',', '.')).astype('float64')
