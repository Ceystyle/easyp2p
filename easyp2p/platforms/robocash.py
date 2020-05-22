# -*- coding: utf-8 -*-
#  Copyright (c) 2018-2020 Niko Sandschneider

"""
Download and parse Robocash statement.

"""

from datetime import date
import json
import time
from typing import Optional, Tuple

from bs4 import BeautifulSoup
import pandas as pd
import requests
from PyQt5.QtCore import QCoreApplication

from easyp2p.p2p_credentials import get_credentials
from easyp2p.p2p_parser import P2PParser
from easyp2p.p2p_signals import Signals

_translate = QCoreApplication.translate


class Robocash:

    """
    Contains methods for downloading/parsing Robocash account statements.
    """

    signals = Signals()

    def __init__(
            self, date_range: Tuple[date, date],
            statement_without_suffix: str,
            signals: Optional[Signals] = None) -> None:
        """
        Constructor of Robocash class.

        Args:
            date_range: Date range (start_date, end_date) for which the account
                statements must be generated.
            statement_without_suffix: File name including path but without
                suffix where the account statement should be saved.
            signals: Signals instance for communicating with the calling class.

        """
        self.name = 'Robocash'
        self.date_range = date_range
        self.statement = statement_without_suffix + '.xls'
        self.signals = signals

    def download_statement(self, _) -> None:
        """
        Generate and download the Robocash account statement for given date
        range.

        Args:
            _: Ignored. This is needed for consistency with platforms that
                use WebDriver to download the statement.

        Raises:
            RuntimeError:
                - If no credentials for Robocash are provided.
                - If login, loading the page, generating or downloading the
                  account statement is not successful.
            RuntimeWarning: If logout is not successful.

        """
        credentials = get_credentials(self.name, self.signals)

        with requests.session() as sess:
            resp = sess.get('https://robo.cash')
            soup = BeautifulSoup(resp.text, 'html.parser')
            token = soup.input.get('value', None)
            if resp.status_code != 200 or token is None:
                raise RuntimeError(_translate(
                    'P2PPlatform',
                    f'{self.name}: loading website was not successful!'))

            data = {
                'email': credentials[0],
                'password': credentials[1],
                '_token': token,
            }
            resp = sess.post('https://robo.cash/login', data=data)
            if resp.status_code != 200:
                raise RuntimeError(_translate(
                    'P2PPlatform', f'{self.name}: login was not successful. '
                                   'Are the credentials correct?'))
            self.signals.update_progress_bar.emit()

            resp = sess.get('https://robo.cash/cabinet/statement')
            soup = BeautifulSoup(resp.text, 'html.parser')
            script = BeautifulSoup(
                soup.find('script', {'id': 'report-template'}).string,
                'html.parser')
            token = script.find('input', {'name': '_token'}).get('value', None)
            if resp.status_code != 200 or token is None:
                raise RuntimeError(_translate(
                    'P2PPlatform',
                    f'{self.name}: loading the account statement page was '
                    f'not successful!'))
            self.signals.update_progress_bar.emit()

            data = {
                '_token': token,
                'currency_id': '1',
                'start_date': self.date_range[0].strftime("%Y-%m-%d"),
                'end_date': self.date_range[1].strftime("%Y-%m-%d"),
                'statement_type': '1'
            }
            resp = sess.post(
                'https://robo.cash/cabinet/statement/generate', data=data)
            if resp.status_code != 200:
                raise RuntimeError(_translate(
                    'P2PPlatform',
                    f'{self.name}: generating the account statement was not '
                    f'successful!'))

            wait_time = 0
            max_wait_time = 30
            while wait_time <= max_wait_time:
                resp = sess.get('https://robo.cash/cabinet/statement')
                soup = BeautifulSoup(resp.text, 'html.parser')
                report = json.loads(
                    soup.find('report-component').get(':initial_report'))
                if report['filename'] is not None:
                    break
                time.sleep(2)
                wait_time += 2
            self.signals.update_progress_bar.emit()

            resp = sess.get(
                f'https://robo.cash/cabinet/statement/{report["id"]}/download')
            if resp.status_code != 200:
                raise RuntimeError(_translate(
                    'P2PPlatform',
                    f'{self.name}: download of account statement failed!'))
            self.signals.update_progress_bar.emit()

            with open(self.statement, 'wb') as file:
                file.write(resp.content)

            resp = sess.get('https://robo.cash/logout')
            if resp.status_code != 200:
                raise RuntimeWarning(_translate(
                    'P2PPlatform', f'{self.name}: logout was not successful!'))
            self.signals.update_progress_bar.emit()

    def parse_statement(self, statement: Optional[str] = None) \
            -> Tuple[pd.DataFrame, Tuple[str, ...]]:
        """
        Parser for Robocash.

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

        # Define mapping between Robocash and easyp2p cash flow types and
        # column names
        cashflow_types = {
            'Adding funds': parser.IN_OUT_PAYMENT,
            'Paying interest': parser.INTEREST_PAYMENT,
            'Purchasing a loan': parser.INVESTMENT_PAYMENT,
            'Returning a loan': parser.REDEMPTION_PAYMENT,
            'Withdrawal of funds': parser.IN_OUT_PAYMENT,
            # We don't report cash transfers within Robocash:
            'Creating a portfolio': parser.IGNORE,
            'Refilling a portfolio': parser.IGNORE,
            'Withdrawing from a portfolio': parser.IGNORE,
        }
        rename_columns = {'Date and time': parser.DATE}

        unknown_cf_types = parser.run(
            '%Y-%m-%d %H:%M:%S', rename_columns, cashflow_types,
            'Operation', 'Amount', "Portfolio's balance")

        return parser.df, unknown_cf_types
