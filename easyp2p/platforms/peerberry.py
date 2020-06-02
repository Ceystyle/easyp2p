#  Copyright (c) 2018-2020 Niko Sandschneider

"""
Download and parse PeerBerry statement.

"""

from datetime import date
import json
from typing import Optional, Tuple

import pandas as pd
from PyQt5.QtCore import QCoreApplication

from easyp2p.p2p_parser import P2PParser
from easyp2p.p2p_session import P2PSession
from easyp2p.p2p_signals import Signals

_translate = QCoreApplication.translate


class PeerBerry:

    """
    Contains methods for downloading/parsing PeerBerry account statements.
    """

    def __init__(
            self, date_range: Tuple[date, date],
            statement_without_suffix: str,
            signals: Optional[Signals] = None) -> None:
        """
        Constructor of PeerBerry class.

        Args:
            date_range: Date range (start_date, end_date) for which the account
                statements must be generated.
            statement_without_suffix: File name including path but without
                suffix where the account statement should be saved.
            signals: Signals instance for communicating with the calling class.

        """
        self.name = 'PeerBerry'
        self.date_range = date_range
        self.statement = statement_without_suffix + '.xlsx'
        self.signals = signals

    def download_statement(self) -> None:
        """
        Generate and download the PeerBerry account statement for given date
        range.

        """
        login_url = 'https://api.peerberry.com/v1/investor/login'
        logout_url = 'https://api.peerberry.com/v1/investor/logout'
        statement_url = (
            f'https://api.peerberry.com/v1/investor/transactions/import?'
            f'startDate={self.date_range[0].strftime("%Y-%m-%d")}&'
            f'endDate={self.date_range[1].strftime("%Y-%m-%d")}&'
            f'transactionType=0&lang=en')

        with P2PSession(self.name, logout_url, self.signals) as sess:
            resp = sess.log_into_page(login_url, 'email', 'password')
            access_token = json.loads(resp.text)['access_token']
            sess.sess.headers = {
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip,deflate,br',
                'Referer': 'https://peerberry.com/en/client/statement',
                'Authorization': f'Bearer {access_token}',
                'Origin': 'https://peerberry.com',
                'Connection': 'keep-alive'
            }
            sess.download_statement(statement_url, self.statement, 'get')

    def parse_statement(self, statement: Optional[str] = None) \
            -> Tuple[pd.DataFrame, Tuple[str, ...]]:
        """
        Parser for Peerberry.

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

        # Define mapping between PeerBerry and easyp2p cash flow types and
        # column names
        cashflow_types = {
            'BUYBACK_INTEREST': parser.BUYBACK_INTEREST_PAYMENT,
            'BUYBACK_PRINCIPAL': parser.BUYBACK_PAYMENT,
            'INVESTMENT': parser.INVESTMENT_PAYMENT,
            'REPAYMENT_INTEREST': parser.INTEREST_PAYMENT,
            'REPAYMENT_PRINCIPAL': parser.REDEMPTION_PAYMENT}
        rename_columns = {'Currency': parser.CURRENCY, 'Date': parser.DATE}

        unknown_cf_types = parser.parse(
            '%Y-%m-%d', rename_columns, cashflow_types, 'Type', 'Amount')

        return parser.df, unknown_cf_types
