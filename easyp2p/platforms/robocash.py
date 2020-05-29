# -*- coding: utf-8 -*-
#  Copyright (c) 2018-2020 Niko Sandschneider

"""
Download and parse Robocash statement.

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
        self.report_id = None
        self.signals = signals

    def download_statement(self) -> None:
        """
        Generate and download the Robocash account statement for given date
        range.

        """
        login_url = 'https://robo.cash/login'
        logout_url = 'https://robo.cash/logout'
        gen_statement_url = 'https://robo.cash/cabinet/statement/generate'
        statement_url = 'https://robo.cash/cabinet/statement'

        with P2PSession(self.name, logout_url, self.signals) as sess:
            data = sess.get_values_from_tag_by_name(
                login_url, 'input', ['_token'], _translate(
                    'P2PPlatform',
                    f'{self.name}: loading website was not successful!'))
            sess.log_into_page(login_url, 'email', 'password', data=data)

            statement_err_msg = _translate(
                'P2PPlatform',
                f'{self.name}: loading the account statement page failed!')
            token = sess.get_value_from_script(
                statement_url, {'id': 'report-template'}, 'input', '_token',
                statement_err_msg)

            data = {
                '_token': token,
                'currency_id': '1',
                'start_date': self.date_range[0].strftime("%Y-%m-%d"),
                'end_date': self.date_range[1].strftime("%Y-%m-%d"),
                'statement_type': '1'
            }
            sess.generate_account_statement(gen_statement_url, 'post', data)

            def download_ready():
                report = json.loads(sess.get_value_from_tag(
                    statement_url, 'report-component', ':initial_report',
                    statement_err_msg))
                if report['filename'] is not None:
                    self.report_id = report['id']
                    return True
                return False

            sess.wait(download_ready)

            sess.download_statement(
                f'https://robo.cash/cabinet/statement/{self.report_id}'
                f'/download', self.statement, 'get')

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

        unknown_cf_types = parser.parse(
            '%Y-%m-%d %H:%M:%S', rename_columns, cashflow_types,
            'Operation', 'Amount', "Portfolio's balance")

        return parser.df, unknown_cf_types
