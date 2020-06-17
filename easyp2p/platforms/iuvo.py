#  Copyright (c) 2018-2020 Niko Sandschneider

"""
Download and parse Iuvo statement.

"""

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By

from easyp2p.p2p_parser import P2PParser
from easyp2p.p2p_webdriver import P2PWebDriver
from easyp2p.platforms.base_platform import BasePlatform


class Iuvo(BasePlatform):
    """
    Contains methods for downloading/parsing Iuvo account statements.
    """

    NAME = 'Iuvo'
    SUFFIX = 'xlsx'

    # Downloader settings
    DOWNLOAD_METHOD = 'webdriver'
    LOGIN_URL = 'https://www.iuvo-group.com/en/login/'
    STATEMENT_URL = 'https://www.iuvo-group.com/en/account-statement/'
    LOGOUT_WAIT_UNTIL_LOC = (By.ID, 'login')
    LOGOUT_LOCATOR = (By.ID, 'p2p_logout')
    HOVER_LOCATOR = (By.LINK_TEXT, 'User name')

    # Parser settings
    DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    RENAME_COLUMNS = {'Date': P2PParser.DATE}
    CASH_FLOW_TYPES = {
        'deposit': P2PParser.IN_OUT_PAYMENT,
        'late_fee': P2PParser.LATE_FEE_PAYMENT,
        'payment_interest': P2PParser.INTEREST_PAYMENT,
        'payment_interest_early': P2PParser.INTEREST_PAYMENT,
        'primary_market_auto_invest': P2PParser.INVESTMENT_PAYMENT,
        'payment_principal_buyback': P2PParser.BUYBACK_PAYMENT,
        'payment_principal': P2PParser.REDEMPTION_PAYMENT,
        'payment_principal_early': P2PParser.REDEMPTION_PAYMENT,
    }
    ORIG_CF_COLUMN = 'Transaction Type'
    VALUE_COLUMN = 'Turnover'
    BALANCE_COLUMN = 'Balance'
    HEADER = 3
    SKIP_FOOTER = 3

    def _webdriver_download(self, webdriver: P2PWebDriver) -> None:
        """
        Generate and download the Iuvo account statement for given date range.

        Args:
            webdriver: P2PWebDriver instance.

        """
        webdriver.log_into_page(
            self.LOGIN_URL, 'login', 'password',
            (By.LINK_TEXT, 'Account Statement'))

        # Click away cookie policy, if present
        webdriver.driver.click_button(
            (By.ID, 'CybotCookiebotDialogBodyButtonAccept'), 'Ignored',
            raise_error=False)

        webdriver.open_account_statement_page(
            self.STATEMENT_URL, (By.ID, 'date_from'))
        soup = BeautifulSoup(webdriver.driver.page_source, 'html.parser')
        try:
            account_id = soup.input["value"]
            p2_var = webdriver.driver.current_url.split(';')[1]
        except (KeyError, IndexError):
            raise RuntimeError(self.errors.load_statement_page_failed)

        webdriver.driver.get(
            f'https://tbp2p.iuvo-group.com/p2p-ui/app?p0=export_file;'
            f'{p2_var};;display_as=export;'
            f'export_as=xlsx;sid=rep_account_statement_full_list;sr=1;'
            f'rep_name=AccountStatement;'
            f'investor_account_id={account_id}&'
            f'date_from={self.date_range[0].strftime("%Y-%m-%d")}&'
            f'date_to={self.date_range[1].strftime("%Y-%m-%d")};'
            f'lang=en_US&screen_width=1920&screen_height=780')

        if not webdriver.download_finished(self.statement):
            raise RuntimeError(self.errors.statement_download_failed)
