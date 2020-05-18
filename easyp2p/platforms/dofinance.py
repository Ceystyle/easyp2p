# -*- coding: utf-8 -*-
#  Copyright (c) 2018-2020 Niko Sandschneider

"""
Download and parse DoFinance statement.

"""

from datetime import date
from typing import Optional, Tuple

from bs4 import BeautifulSoup
import pandas as pd
from PyQt5.QtCore import QCoreApplication
import requests

from easyp2p.p2p_credentials import get_credentials
from easyp2p.p2p_parser import P2PParser
from easyp2p.p2p_signals import Signals

_translate = QCoreApplication.translate


class DoFinance:

    """
    Contains methods for downloading/parsing DoFinance account statements.
    """

    def __init__(
            self, date_range: Tuple[date, date], statement_without_suffix: str,
            signals: Optional[Signals] = None) -> None:
        """
        Constructor of DoFinance class.

        Args:
            date_range: Date range (start_date, end_date) for which the account
                statements must be generated.
            statement_without_suffix: File name including path but without
                suffix where the account statement should be saved.
            signals: Signals instance for communicating with the calling class.

        """
        self.name = 'DoFinance'
        self.date_range = date_range
        self.statement = statement_without_suffix + '.xlsx'
        self.signals = signals

    def download_statement(self, _) -> None:
        """
        Generate and download the DoFinance account statement for given date
        range.

        Args:
            _: Ignored. This is needed for consistency with platforms that
                use WebDriver to download the statement.

        Raises:
            RuntimeError:
                - If no credentials for DoFinance are provided.
                - If login or downloading the account statement is not
                successful.
            RuntimeWarning: If logout is not successful.

        """
        credentials = get_credentials(self.name, self.signals)

        with requests.session() as sess:
            resp = sess.get('https://www.dofinance.eu/en/users/login')
            soup = BeautifulSoup(resp.text, 'html.parser')
            data = {
                '_method': 'POST',
                'email': credentials[0],
                'password': credentials[1],
            }
            token_names = ['_Token[fields]', '_Token[unlocked]']
            inputs = soup.find_all('input')
            for elem in inputs:
                if elem['name'] in token_names:
                    data[elem['name']] = elem['value']

            resp = sess.post(
                'https://www.dofinance.eu/en/users/login', data=data)
            if resp.status_code != 200:
                raise RuntimeError(_translate(
                    'P2PPlatform', f'{self.name}: login was not successful. '
                    'Are the credentials correct?'))
            self.signals.update_progress_bar.emit()

            resp = sess.get('https://www.dofinance.eu/en/users/statement')
            if resp.status_code != 200:
                raise RuntimeError(_translate(
                    'P2PPlatform',
                    f'{self.name}: loading account statement page was not '
                    f'successful!'))
            self.signals.update_progress_bar.emit()

            data = {
                '_method': 'PUT',
                'date_from': self.date_range[0].strftime('%d.%m.%Y'),
                'date_to': self.date_range[1].strftime('%d.%m.%Y'),
                'trans_type': '',
                'xls': 'Download+XLS',
            }
            soup = BeautifulSoup(resp.text, 'html.parser')
            inputs = soup.find_all('input')
            for elem in inputs:
                if elem['name'] in token_names:
                    data[elem['name']] = elem['value']

            resp = sess.post(
                'https://www.dofinance.eu/en/users/statement', data=data)
            if resp.status_code != 200:
                raise RuntimeError(_translate(
                    'P2PPlatform',
                    f'{self.name}: download of account statement failed!'))

            with open(self.statement, 'wb') as file:
                file.write(resp.content)

            resp = sess.get('https://www.dofinance.eu/en/users/logout')
            if resp.status_code != 200:
                raise RuntimeWarning(_translate(
                    'P2PPlatform', f'{self.name}: logout was not successful!'))
            self.signals.update_progress_bar.emit()

    def parse_statement(self, statement: Optional[str] = None) \
            -> Tuple[pd.DataFrame, Tuple[str, ...]]:
        """
        Parser for DoFinance.

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
            self.name, self.date_range, self.statement, skipfooter=2,
            signals=self.signals)

        # Define mapping between DoFinance and easyp2p cash flow types and
        # column names
        cashflow_types = {
            'Withdrawal': parser.IN_OUT_PAYMENT,
            'Profit': parser.INTEREST_PAYMENT,
            # treat bonus payments as interest payments
            'Investor Bonus': parser.INTEREST_PAYMENT}

        for cf_type in parser.df['Transaction Type'].unique():
            if cf_type.startswith('Repayment'):
                cashflow_types[cf_type] = parser.REDEMPTION_PAYMENT
            elif cf_type.startswith('Investment'):
                cashflow_types[cf_type] = parser.INVESTMENT_PAYMENT
            elif cf_type.startswith('Funding'):
                cashflow_types[cf_type] = parser.IN_OUT_PAYMENT

        rename_columns = {'Processing Date': parser.DATE}

        unknown_cf_types = parser.run(
            '%d.%m.%Y', rename_columns, cashflow_types, 'Transaction Type',
            'Amount, €')

        return parser.df, unknown_cf_types
