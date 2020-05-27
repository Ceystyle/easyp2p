# -*- coding: utf-8 -*-
#  Copyright (c) 2018-2020 Niko Sandschneider

"""
Download and parse Bondora statement.

"""

from datetime import date
from typing import Optional, Tuple

import pandas as pd
from PyQt5.QtCore import QCoreApplication

from easyp2p.p2p_parser import P2PParser
from easyp2p.p2p_session import P2PSession
from easyp2p.p2p_signals import Signals

_translate = QCoreApplication.translate


class Bondora:

    """Contains methods for downloading/parsing Bondora account statements."""

    def __init__(
            self, date_range: Tuple[date, date],
            statement_without_suffix: str,
            signals: Optional[Signals] = None) -> None:
        """
        Constructor of Bondora class.

        Args:
            date_range: Date range (start_date, end_date) for which the account
                statements must be generated.
            statement_without_suffix: File name including path but without
                suffix where the account statement should be saved.
            signals: Signals instance for communicating with the calling class.

        """
        self.name = 'Bondora'
        self.date_range = date_range
        self.statement = statement_without_suffix + '.xlsx'
        self.signals = signals

    def download_statement(self, _) -> None:
        """
        Generate and download the Bondora account statement for given date
        range.

        Args:
            _: Ignored. This is needed for consistency with platforms that
                use WebDriver to download the statement.

        """
        login_url = 'https://www.bondora.com/en/login/'

        with P2PSession(
                self.name, 'https://www.bondora.com/en/authorize/logout/',
                self.signals) as sess:

            token_field = '__RequestVerificationToken'
            data = sess.get_values_from_tag_by_name(
                login_url, 'input', [token_field], _translate(
                    'P2PPlatform',
                    f'{self.name}: loading login page was not successful!'))

            sess.log_into_page(login_url, 'Email', 'Password', data)

            dates = {
                'StartYear': self.date_range[0].strftime('%Y'),
                'StartMonth': self.date_range[0].strftime('%-m'),
                'EndYear': self.date_range[1].strftime('%Y'),
                'EndMonth': self.date_range[1].strftime('%-m'),
            }
            url = 'https://www.bondora.com/en/cashflow/searchcashflow?'
            for key, value in dates.items():
                url += str(key) + '=' + str(value) + '&'
            url += 'downloadExcel=true'
            sess.download_statement(url, self.statement, 'get')

    def parse_statement(self, statement: Optional[str] = None) \
            -> Tuple[pd.DataFrame, Tuple[str, ...]]:
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

        parser = P2PParser(
            self.name, self.date_range, self.statement, signals=self.signals)

        # Calculate defaulted payments
        parser.df[parser.DEFAULTS] = (
            parser.df['Principal received - total']
            - parser.df['Principal planned - total'])

        # Define mapping between Bondora and easyp2p column names
        rename_columns = {
            'Net capital deployed': parser.IN_OUT_PAYMENT,
            'Closing balance': parser.END_BALANCE_NAME,
            'Principal received - total': parser.REDEMPTION_PAYMENT,
            'Interest received - total': parser.INTEREST_PAYMENT,
            'Net loan investments': parser.INVESTMENT_PAYMENT,
            'Opening balance': parser.START_BALANCE_NAME,
            'Period': parser.DATE}

        unknown_cf_types = parser.run('%d.%m.%Y', rename_columns=rename_columns)

        return parser.df, unknown_cf_types
