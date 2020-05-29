#  Copyright (c) 2018-2020 Niko Sandschneider

"""
Download and parse Iuvo statement.

"""

from datetime import date
from typing import Optional, Tuple

from bs4 import BeautifulSoup
import pandas as pd
from PyQt5.QtCore import QCoreApplication
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from easyp2p.p2p_parser import P2PParser
from easyp2p.p2p_platform import P2PPlatform, download_finished
from easyp2p.p2p_signals import Signals

_translate = QCoreApplication.translate


class Iuvo:
    """
    Contains methods for downloading/parsing Iuvo account statements.
    """

    def __init__(
            self, date_range: Tuple[date, date],
            statement_without_suffix: str,
            signals: Optional[Signals] = None) -> None:
        """
        Constructor of Iuvo class.

        Args:
            date_range: Date range (start_date, end_date) for which the account
                statements must be generated.
            statement_without_suffix: File name including path but without
                suffix where the account statement should be saved.
            signals: Signals instance for communicating with the calling class.

        """
        self.name = 'Iuvo'
        self.date_range = date_range
        self.statement = statement_without_suffix + '.xlsx'
        self.signals = signals

    def download_statement(self, headless: bool) -> None:
        """
        Generate and download the Iuvo account statement for given date range.

        Args:
            headless: If True use ChromeDriver in headless mode, if False not.

        """
        urls = {
            'login': 'https://www.iuvo-group.com/en/login/',
            'statement': 'https://www.iuvo-group.com/en/account-statement/',
        }

        with P2PPlatform(
                self.name, headless, urls,
                EC.element_to_be_clickable((By.ID, 'login')),
                logout_locator=(By.ID, 'p2p_logout'),
                hover_locator=(By.LINK_TEXT, 'User name'),
                signals=self.signals) as iuvo:

            iuvo.log_into_page(
                'login', 'password',
                EC.element_to_be_clickable((By.LINK_TEXT, 'Account Statement')))

            # Click away cookie policy, if present
            iuvo.driver.click_button(
                (By.ID, 'CybotCookiebotDialogBodyButtonAccept'), 'Ignored',
                raise_error=False)

            iuvo.open_account_statement_page((By.ID, 'date_from'))
            soup = BeautifulSoup(iuvo.driver.page_source, 'html.parser')
            try:
                account_id = soup.input["value"]
                p2_var = iuvo.driver.current_url.split(';')[1]
            except (KeyError, IndexError):
                raise RuntimeError(_translate(
                    'P2PPlatform',
                    f'{self.name}: loading account statement page was not '
                    'successful!'))

            iuvo.driver.get(
                f'https://tbp2p.iuvo-group.com/p2p-ui/app?p0=export_file;'
                f'{p2_var};;display_as=export;'
                f'export_as=xlsx;sid=rep_account_statement_full_list;sr=1;'
                f'rep_name=AccountStatement;'
                f'investor_account_id={account_id}&'
                f'date_from={self.date_range[0].strftime("%Y-%m-%d")}&'
                f'date_to={self.date_range[1].strftime("%Y-%m-%d")};'
                f'lang=en_US&screen_width=1920&screen_height=780')

            if not download_finished(
                    self.statement, iuvo.driver.download_directory):
                raise RuntimeError(_translate(
                    'P2PPlatform',
                    f'{self.name}: download of account statement failed!'))

    def parse_statement(self, statement: Optional[str] = None) \
            -> Tuple[pd.DataFrame, Tuple[str, ...]]:
        """
        Parser for Iuvo.

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
            self.name, self.date_range, self.statement, header=3, skipfooter=3,
            signals=self.signals)

        # Define mapping between Iuvo and easyp2p cashflow types and column
        # names
        cashflow_types = {
            'deposit': parser.IN_OUT_PAYMENT,
            'late_fee': parser.LATE_FEE_PAYMENT,
            'payment_interest': parser.INTEREST_PAYMENT,
            'payment_interest_early': parser.INTEREST_PAYMENT,
            'primary_market_auto_invest': parser.INVESTMENT_PAYMENT,
            'payment_principal_buyback': parser.BUYBACK_PAYMENT,
            'payment_principal': parser.REDEMPTION_PAYMENT,
            'payment_principal_early': parser.REDEMPTION_PAYMENT}
        rename_columns = {'Date': parser.DATE}

        unknown_cf_types = parser.parse(
            '%Y-%m-%d %H:%M:%S', rename_columns, cashflow_types,
            'Transaction Type', 'Turnover', 'Balance')

        return parser.df, unknown_cf_types
