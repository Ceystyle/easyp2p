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

    # Parser settings
    DATE_FORMAT = '%d.%m.%Y'
    RENAME_COLUMNS = {
        'Date': P2PParser.DATE,
        'Currency': P2PParser.CURRENCY,
    }
    CASH_FLOW_TYPES = {
        # Treat cashback as interest payment:
        'Cashback': P2PParser.INTEREST_PAYMENT,
        'Deposit': P2PParser.IN_OUT_PAYMENT,
        'Withdrawal': P2PParser.IN_OUT_PAYMENT,
        'Interest': P2PParser.INTEREST_PAYMENT,
        'Investment': P2PParser.INVESTMENT_PAYMENT,
        'Principal': P2PParser.REDEMPTION_PAYMENT,
    }
    ORIG_CF_COLUMN = 'Type'
    VALUE_COLUMN = 'Amount'
    BALANCE_COLUMN = 'Balance'

    def _webdriver_download(self, headless: bool) -> None:
        """
        Generate and download the Grupeer account statement for given date
        range.

        Args:
            headless: If True use ChromeDriver in headless mode, if False not.

        """
        urls = {
            'login': 'https://www.grupeer.com/login',
            'statement': ('https://www.grupeer.com/account-statement'
                          '?currency_code=eur'),
        }

        with P2PWebDriver(
                self.NAME, headless, urls,
                EC.element_to_be_clickable((By.LINK_TEXT, 'Sign In')),
                logout_locator=(By.LINK_TEXT, 'Logout'),
                hover_locator=(By.CLASS_NAME, 'header-auth-menu-name'),
                signals=self.signals) as grupeer:

            grupeer.log_into_page('email', 'password', None)
            grupeer.wait_for_captcha(
                (By.CLASS_NAME, 'text-danger'),
                'These credentials do not match our records.')

            grupeer.open_account_statement_page((By.ID, 'from'))

            grupeer.generate_statement_direct(
                self.date_range, (By.ID, 'from'), (By.ID, 'to'), '%d.%m.%Y',
                wait_until=EC.text_to_be_present_in_element(
                    (By.CLASS_NAME, 'balance-block'),
                    'Starting balance on '
                    + str(self.date_range[0].strftime('%d.%m.%Y'))),
                submit_btn_locator=(By.NAME, 'submit'))

            grupeer.download_statement(self.statement, (By.NAME, 'excel'))

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
