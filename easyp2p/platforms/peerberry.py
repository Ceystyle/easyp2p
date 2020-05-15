#  Copyright (c) 2018-2020 Niko Sandschneider

"""
Download and parse PeerBerry statement.

"""

from datetime import date
import json
from typing import Optional, Tuple

import pandas as pd
from PyQt5.QtCore import QCoreApplication
import requests

from easyp2p.p2p_parser import P2PParser
from easyp2p.p2p_credentials import get_credentials_from_keyring
from easyp2p.p2p_signals import Signals, CredentialReceiver

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

    def download_statement(self, _) -> None:
        """
        Generate and download the PeerBerry account statement for given date
        range.

        Args:
            _: Ignored. This is needed for consistency with platforms that
                use WebDriver to download the statement.

        Raises:
            RuntimeError:
                - If no credentials for PeerBerry are provided.
                - If login or downloading the account statement is not
                successful.
            RuntimeWarning: If logout is not successful.

        """
        credentials = get_credentials_from_keyring(self.name)
        if credentials is None:
            credential_receiver = CredentialReceiver(self.signals)
            credentials = credential_receiver.wait_for_credentials(self.name)

        if credentials[0] == '' or credentials[1] == '':
            raise RuntimeError(_translate(
                'P2PPlatform',
                f'No credentials for {self.name} provided! Aborting!'))

        with requests.session() as sess:
            data = {
                'email': credentials[0],
                'password': credentials[1],
                'params': (
                    "{\"pbLastCookie\":\"https://peerberry.com/\","
                    "\"pbFirstCookie\":\"/\"}")}
            resp = sess.post(
                'https://api.peerberry.com/v1/investor/login', data=data)
            if resp.status_code != 200:
                raise RuntimeError(_translate(
                    'P2PPlatform', f'{self.name}: login was not successful. '
                    'Are the credentials correct?'))
            self.signals.update_progress_bar.emit()

            access_token = json.loads(resp.text)['access_token']
            header = {
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip,deflate,br',
                'Referer': 'https://peerberry.com/en/client/statement',
                'Authorization': f'Bearer {access_token}',
                'Origin': 'https://peerberry.com',
                'Connection': 'keep-alive'
            }

            resp = sess.get(
                f'https://api.peerberry.com/v1/investor/transactions/import?'
                f'startDate={self.date_range[0].strftime("%Y-%m-%d")}&'
                f'endDate={self.date_range[1].strftime("%Y-%m-%d")}&'
                f'transactionType=0&lang=en', headers=header)
            if resp.status_code != 200:
                raise RuntimeError(_translate(
                    'P2PPlatform',
                    f'{self.name}: download of account statement failed!'))

            with open(self.statement, 'bw') as file:
                file.write(resp.content)

            resp = sess.get(
                'https://api.peerberry.com/v1/investor/logout',
                headers=header)
            if resp.status_code != 200:
                raise RuntimeWarning(_translate(
                    'P2PPlatform', f'{self.name}: logout was not successful!'))
            self.signals.update_progress_bar.emit()

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
        rename_columns = {'Currency Id': parser.CURRENCY, 'Date': parser.DATE}

        unknown_cf_types = parser.run(
            '%Y-%m-%d', rename_columns, cashflow_types, 'Type', 'Amount')

        return parser.df, unknown_cf_types
