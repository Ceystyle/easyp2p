#  Copyright (c) 2018-2020 Niko Sandschneider

"""
Implements BasePlatform, the parent class for all P2P platforms. It contains
two public methods:

* download_statement: For downloading the account statement for a given date
    range. This needs to be implemented by each child class separately.
* parse_statement: For parsing the downloaded account statement file.
    BasePlatform includes an implementation of this method which can be re-used
    by child classes.

"""

from datetime import date
from typing import Optional, Tuple

import pandas as pd

from easyp2p.p2p_parser import P2PParser
from easyp2p.p2p_session import P2PSession
from easyp2p.p2p_signals import Signals, PlatformFailedError
from easyp2p.p2p_webdriver import P2PWebDriver
from easyp2p.errors import PlatformErrors


class BasePlatform:

    """BasePlatform is the parent class for all P2P platforms."""

    NAME = None
    SUFFIX = None

    # Downloader settings
    DOWNLOAD_METHOD = None  # Possible values are: webdriver, recaptcha, session
    JSON = False
    LOGIN_URL = None
    LOGOUT_URL = None
    GEN_STATEMENT_URL = None
    STATEMENT_URL = None
    LOGOUT_WAIT_UNTIL_LOC = None
    LOGOUT_LOCATOR = None
    HOVER_LOCATOR = None

    # Parser settings
    DATE_FORMAT = None
    RENAME_COLUMNS = None
    CASH_FLOW_TYPES = None
    ORIG_CF_COLUMN = None
    VALUE_COLUMN = None
    BALANCE_COLUMN = None
    HEADER = 0
    SKIP_FOOTER = 0

    def __init__(
            self, date_range: Tuple[date, date],
            statement_without_suffix: str,
            signals: Optional[Signals] = None) -> None:
        """
        Constructor of BasePlatform class.

        Args:
            date_range: Date range (start_date, end_date) for which the account
                statements must be generated.
            statement_without_suffix: File name including path but without
                suffix where the account statement should be saved.
            signals: Signals instance for communicating with the calling class.
                Default is None.

        """
        self.date_range = date_range
        self.statement = '.'.join([statement_without_suffix, self.SUFFIX])
        self.signals = signals
        self.errors = PlatformErrors(self.NAME)

    def download_statement(self, headless: bool = True) -> None:
        """
        Common download method for all platforms. Depending on the chosen
        DOWNLOAD_METHOD it calls the correct download method.

        Args:
            headless: If True use Chromedriver in headless mode. Only relevant
                for platforms that use P2PWebDriver.

        """
        if self.DOWNLOAD_METHOD in ('webdriver', 'recaptcha'):
            if self.DOWNLOAD_METHOD == 'recaptcha':
                headless = False

            with P2PWebDriver(
                    self.NAME, headless, self.LOGOUT_WAIT_UNTIL_LOC,
                    logout_url=self.LOGOUT_URL,
                    logout_locator=self.LOGOUT_LOCATOR,
                    hover_locator=self.HOVER_LOCATOR,
                    signals=self.signals) as webdriver:
                self._webdriver_download(webdriver)
        elif self.DOWNLOAD_METHOD == 'session':
            with P2PSession(
                    self.NAME, self.LOGOUT_URL, self.signals,
                    json=self.JSON) as sess:
                self._session_download(sess)
        else:
            raise PlatformFailedError(
                f'{self.NAME}: invalid download method provided: '
                f'{self.DOWNLOAD_METHOD}!')

    def _webdriver_download(self, webdriver: P2PWebDriver) -> None:
        """
        Every child class using P2PWebdriver needs to override this method for
        downloading the account statement.

        Args:
            webdriver: P2PWebDriver instance.

        """
        raise PlatformFailedError(
            f'{self.NAME}: no override of _webdriver_download!')

    def _session_download(self, sess: P2PSession) -> None:
        """
        Every child class using P2PSession needs to override this method for
        downloading the account statement.

        Args:
            sess: P2PSession instance.

        """
        raise PlatformFailedError(
            f'{self.NAME}: no override of _session_download!')

    def parse_statement(self, statement: Optional[str] = None) \
            -> Tuple[pd.DataFrame, Tuple[str, ...]]:
        """
        Parses the account statement.

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
            self.NAME, self.date_range, self.statement, header=self.HEADER,
            skipfooter=self.SKIP_FOOTER, signals=self.signals)

        self._transform_df(parser)

        unknown_cf_types = parser.parse(
            self.DATE_FORMAT, self.RENAME_COLUMNS, self.CASH_FLOW_TYPES,
            self.ORIG_CF_COLUMN, self.VALUE_COLUMN, self.BALANCE_COLUMN)

        return parser.df, unknown_cf_types

    def _transform_df(self, parser: P2PParser) -> None:
        """
        Overriding this method allows to include additional transformation of
        the parser data frame which are necessary for some platforms. By default
        this method does nothing.

        Args:
            parser: P2PParser instance.

        """
