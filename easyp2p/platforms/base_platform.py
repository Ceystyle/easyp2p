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
from easyp2p.p2p_signals import Signals, PlatformFailedError


class BasePlatform:

    """BasePlatform is the parent class for all P2P platforms."""

    NAME = None
    SUFFIX = None
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

    def download_statement(self, *args) -> None:
        """
        Every child class needs to override download_statement for downloading
        the account statement.

        """
        raise PlatformFailedError(
            f'{self.NAME}: download_statement needs an override!')

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
